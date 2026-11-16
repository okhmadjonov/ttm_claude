from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.modules.auth.models import RefreshToken, User, UserRole
from app.modules.auth.schemas import UserCreate
from app.modules.organizations import service as organizations_service

DUMMY_HASH = hash_password("dummy-password")


class AuthError(Exception):
    """Raised when credentials or tokens are invalid."""


class UserRuleError(Exception):
    """Raised when a user rule is violated."""


def get_user(db: Session, user_id: int) -> User | None:
    user = db.get(User, user_id)
    if user is None or user.is_deleted:
        return None
    return user


def get_user_by_username(db: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username, User.is_deleted.is_(False))
    return db.scalar(stmt)


def create_user(db: Session, data: UserCreate, created_by_id: int | None = None) -> User:
    if db.scalar(select(User.id).where(User.username == data.username)) is not None:
        raise UserRuleError("Username already taken")

    if data.role == UserRole.superadmin:
        if data.organization_id is not None:
            raise UserRuleError("Superadmin cannot belong to an organization")
    else:
        if data.organization_id is None:
            raise UserRuleError(f"{data.role.value} requires an organization")
        org = organizations_service.get_organization(db, data.organization_id)
        if org is None:
            raise UserRuleError("Organization not found")
        if org.level.value != data.role.value:
            raise UserRuleError(
                f"Role {data.role.value} requires a {data.role.value} level organization"
            )

    user = User(
        full_name=data.full_name,
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
        organization_id=data.organization_id,
        created_by_id=created_by_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    db.commit()
    return access_token, refresh_token


def login(db: Session, username: str, password: str) -> tuple[str, str]:
    user = get_user_by_username(db, username)
    if user is None:
        verify_password(password, DUMMY_HASH)
        raise AuthError("Invalid username or password")
    if not verify_password(password, user.password_hash):
        raise AuthError("Invalid username or password")
    if not user.is_active:
        raise AuthError("User is inactive")
    return issue_tokens(db, user)


def refresh(db: Session, refresh_token: str) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(refresh_token)
        )
    )
    if token is None:
        raise AuthError("Invalid refresh token")

    if token.revoked_at is not None:
        active_tokens = db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == token.user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        for active in active_tokens:
            active.revoked_at = now
        db.commit()
        raise AuthError("Refresh token was already used")

    if token.expires_at < now:
        raise AuthError("Refresh token expired")

    user = get_user(db, token.user_id)
    if user is None or not user.is_active:
        raise AuthError("User is inactive")

    token.revoked_at = now
    return issue_tokens(db, user)


def logout(db: Session, refresh_token: str) -> None:
    token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(refresh_token)
        )
    )
    if token is not None and token.revoked_at is None:
        token.revoked_at = datetime.now(timezone.utc)
        db.commit()
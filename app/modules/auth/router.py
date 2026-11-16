from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth import service
from app.modules.auth.dependencies import get_current_user, require_roles
from app.modules.auth.models import User, UserRole
from app.modules.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        access_token, refresh_token = service.login(db, data.username, data.password)
    except service.AuthError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        access_token, refresh_token = service.refresh(db, data.refresh_token)
    except service.AuthError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, db: Session = Depends(get_db)):
    service.logout(db, data.refresh_token)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.superadmin)),
):
    try:
        return service.create_user(db, data, created_by_id=current_user.id)
    except service.UserRuleError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
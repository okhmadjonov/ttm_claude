from sqlalchemy.orm import Session

from app.modules.auth.models import User, UserRole
from app.modules.organizations import service as organizations_service


def get_visible_org_ids(db: Session, user: User) -> list[int] | None:
    """Return organization ids the user may see, or None if unrestricted."""
    if user.role in (UserRole.superadmin, UserRole.ministry):
        return None
    if user.organization_id is None:
        return []
    return organizations_service.get_subtree_ids(db, user.organization_id)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import require_roles
from app.modules.auth.models import User, UserRole
from app.modules.organizations import service
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])

require_superadmin = require_roles(UserRole.superadmin)
require_full_view = require_roles(UserRole.superadmin, UserRole.ministry)


@router.get("/", response_model=list[OrganizationRead])
def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_full_view),
):
    return service.get_organizations(db, skip, limit)


@router.get("/{org_id}", response_model=OrganizationRead)
def read_organization(
    org_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_full_view),
):
    org = service.get_organization(db, org_id)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")
    return org


@router.post("/", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    try:
        return service.create_organization(db, data, current_user.id)
    except service.OrganizationRuleError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.patch("/{org_id}", response_model=OrganizationRead)
def update_organization(
    org_id: int,
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    org = service.get_organization(db, org_id)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")
    return service.update_organization(db, org, data, current_user.id)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    org = service.get_organization(db, org_id)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")
    try:
        service.delete_organization(db, org, current_user.id)
    except service.OrganizationRuleError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
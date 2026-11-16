from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.organizations.models import Organization, OrganizationLevel
from app.modules.organizations.schemas import OrganizationCreate, OrganizationUpdate

REQUIRED_PARENT_LEVEL = {
    OrganizationLevel.ministry: None,
    OrganizationLevel.region: OrganizationLevel.ministry,
    OrganizationLevel.district: OrganizationLevel.region,
    OrganizationLevel.branch: OrganizationLevel.district,
}


class OrganizationRuleError(Exception):
    """Raised when an organization tree rule is violated."""


def get_organizations(
    db: Session,
    visible_ids: list[int] | None,
    skip: int = 0,
    limit: int = 50,
) -> list[Organization]:
    stmt = select(Organization).where(Organization.is_deleted.is_(False))
    if visible_ids is not None:
        stmt = stmt.where(Organization.id.in_(visible_ids))
    stmt = stmt.order_by(Organization.id).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def get_organization(db: Session, org_id: int) -> Organization | None:
    org = db.get(Organization, org_id)
    if org is None or org.is_deleted:
        return None
    return org


def create_organization(
    db: Session, data: OrganizationCreate, user_id: int
) -> Organization:
    required_level = REQUIRED_PARENT_LEVEL[data.level]

    if required_level is None:
        if data.parent_id is not None:
            raise OrganizationRuleError("Ministry cannot have a parent")
    else:
        if data.parent_id is None:
            raise OrganizationRuleError(f"{data.level.value} requires a parent")
        parent = get_organization(db, data.parent_id)
        if parent is None:
            raise OrganizationRuleError("Parent organization not found")
        if parent.level != required_level:
            raise OrganizationRuleError(
                f"Parent of {data.level.value} must be {required_level.value}"
            )

    org = Organization(
        **data.model_dump(),
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

def update_organization(
    db: Session, org: Organization, data: OrganizationUpdate, user_id: int
) -> Organization:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(org, field, value)
    org.updated_by_id = user_id
    db.commit()
    db.refresh(org)
    return org

def delete_organization(db: Session, org: Organization, user_id: int) -> None:
    has_children = db.scalar(
        select(Organization.id)
        .where(Organization.parent_id == org.id, Organization.is_deleted.is_(False))
        .limit(1)
    )
    if has_children is not None:
        raise OrganizationRuleError("Organization has child organizations")

    org.is_deleted = True
    org.updated_by_id = user_id
    db.commit()



def get_subtree_ids(db: Session, root_id: int) -> list[int]:
    tree = (
        select(Organization.id)
        .where(Organization.id == root_id, Organization.is_deleted.is_(False))
        .cte("org_tree", recursive=True)
    )
    tree = tree.union_all(
        select(Organization.id)
        .join(tree, Organization.parent_id == tree.c.id)
        .where(Organization.is_deleted.is_(False))
    )
    return list(db.scalars(select(tree.c.id)))
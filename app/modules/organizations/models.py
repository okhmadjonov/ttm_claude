import enum

from sqlalchemy import Boolean, Enum, ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column
from app.core.mixins import AuditMixin, SoftDeleteMixin, TimestampMixin
from app.core.database import Base
from app.core.mixins import SoftDeleteMixin, TimestampMixin


class OrganizationLevel(str, enum.Enum):
    warehouse = "warehouse"
    ministry = "ministry"
    region = "region"
    district = "district"
    branch = "branch"

class Organization(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    level: Mapped[OrganizationLevel] = mapped_column(
        Enum(OrganizationLevel, native_enum=False, length=20)
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
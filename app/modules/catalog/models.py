from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.mixins import AuditMixin, SoftDeleteMixin, TimestampMixin


class ProductCategory(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_categories.id"), index=True
    )
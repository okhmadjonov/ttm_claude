from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, false, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=false(), index=True
    )


class AuditMixin:
    @declared_attr
    def created_by_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("users.id"), index=True)

    @declared_attr
    def updated_by_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("users.id"), index=True)
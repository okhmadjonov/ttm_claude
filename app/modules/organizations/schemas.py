from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.organizations.models import OrganizationLevel


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    level: OrganizationLevel
    parent_id: int | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    is_active: bool | None = None


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    level: OrganizationLevel
    parent_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
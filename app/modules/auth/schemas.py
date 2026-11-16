from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.auth.models import UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.]+$")
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    organization_id: int | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    username: str
    role: UserRole
    organization_id: int | None
    is_active: bool
    created_at: datetime
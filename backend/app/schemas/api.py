from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.domain import AuthorizationType, UserRole


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class ProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class OfficialSourcePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    url: str
    last_reform_date: date | None


class AgentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    plate: str
    full_name: str
    authorization_type: AuthorizationType
    corporation: str | None
    alcaldias: list[str] | None


class AgentSearchResponse(BaseModel):
    query: str
    matched_by: Literal["plate", "name"]
    results: list[AgentPublic]
    source: OfficialSourcePublic | None

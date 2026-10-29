from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field, computed_field

from app.models.domain import AuthorizationType, UserRole


def _normalise_email(value):
    return value.strip().lower() if isinstance(value, str) else value


# Addresses are compared case-insensitively, so they are trimmed and lowercased on the way in.
NormalisedEmail = Annotated[EmailStr, BeforeValidator(_normalise_email)]


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    email_verified: bool
    created_at: datetime
    # Read from the ORM object only to derive has_password; never serialised.
    password_hash: str | None = Field(default=None, exclude=True, repr=False)

    @computed_field
    @property
    def has_password(self) -> bool:
        return self.password_hash is not None


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: NormalisedEmail
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: NormalisedEmail
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=20, max_length=4096)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class ProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: NormalisedEmail | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    current_password: str | None = Field(default=None, max_length=128)  # required to change the email or the password


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

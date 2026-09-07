from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.domain import UserRole


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


class AgentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plate: str
    name: str


class FeedbackRequest(BaseModel):
    response_id: int
    rating: int = Field(ge=1, le=5)


class LegalConsultationRequest(BaseModel):
    question: str = Field(min_length=3, max_length=5000)


class Citation(BaseModel):
    document: str
    page: str | int | None = None


class LegalConsultationResponse(BaseModel):
    response_id: int
    answer: str
    category: str
    citations: list[Citation]

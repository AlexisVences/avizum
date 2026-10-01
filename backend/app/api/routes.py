from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select

from app.api.deps import AdminUser, CurrentUser, DbSession, OptionalUser
from app.core.security import create_access_token, hash_password, verify_password
from app.models.domain import AgentLookup, AuthorizedAgent, Consultation, Feedback, LegalResponse, User
from app.schemas.api import (AdminUserUpdate, AgentPublic, FeedbackRequest, LegalConsultationRequest, LegalConsultationResponse, LoginRequest, ProfileUpdate, RegisterRequest, TokenResponse, UserPublic)
from app.services.legal_ai import LegalAIService, LegalAIUnavailable
from app.core.config import get_settings

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> User:
    exists = db.scalar(select(User.id).where(User.email == str(payload.email)))
    if exists:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(first_name=payload.first_name, last_name=payload.last_name, email=str(payload.email), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email)))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)


@router.get("/users/me", response_model=UserPublic)
def read_profile(user: CurrentUser) -> User:
    return user


@router.patch("/users/me", response_model=UserPublic)
def update_profile(payload: ProfileUpdate, user: CurrentUser, db: DbSession) -> User:
    values = payload.model_dump(exclude_unset=True)
    if "email" in values:
        email = str(values["email"])
        other = db.scalar(select(User.id).where(User.email == email, User.id != user.id))
        if other:
            raise HTTPException(status_code=409, detail="Email is already registered")
        user.email = email
    for field in ("first_name", "last_name"):
        if field in values:
            setattr(user, field, values[field])
    if password := values.get("password"):
        user.password_hash = hash_password(password)
    db.commit()
    db.refresh(user)
    return user


@router.get("/admin/users", response_model=list[UserPublic])
def list_users(_: AdminUser, db: DbSession) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


@router.patch("/admin/users/{user_id}", response_model=UserPublic)
def manage_user(user_id: int, payload: AdminUserUpdate, _: AdminUser, db: DbSession) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(target, field, value)
    db.commit()
    db.refresh(target)
    return target


@router.get("/agents/{plate}", response_model=AgentPublic)
def lookup_agent(plate: str, user: OptionalUser, db: DbSession) -> AuthorizedAgent:
    normalized = plate.strip().upper()
    agent = db.scalar(select(AuthorizedAgent).where(AuthorizedAgent.plate == normalized))
    if agent is None:
        raise HTTPException(status_code=404, detail="Authorized agent not found")
    db.add(AgentLookup(user_id=user.id if user else None, agent_id=agent.id))
    db.commit()
    return agent


@router.post("/legal-consultations", response_model=LegalConsultationResponse, status_code=status.HTTP_201_CREATED)
def legal_consultation(payload: LegalConsultationRequest, user: CurrentUser, db: DbSession) -> LegalConsultationResponse:
    try:
        generated = LegalAIService(get_settings()).answer(payload.question)
    except LegalAIUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    consultation = Consultation(user_id=user.id, question=payload.question)
    db.add(consultation)
    db.flush()
    answer = LegalResponse(consultation_id=consultation.id, text=generated.answer, category=generated.category)
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return LegalConsultationResponse(response_id=answer.id, answer=answer.text, category=answer.category, citations=generated.citations)


@router.put("/legal-responses/{response_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
def submit_feedback(response_id: int, payload: FeedbackRequest, user: CurrentUser, db: DbSession) -> Response:
    if payload.response_id != response_id:
        raise HTTPException(status_code=422, detail="Response ID must match the URL")
    response = db.get(LegalResponse, response_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Legal response not found")
    consultation = db.get(Consultation, response.consultation_id)
    if consultation is None or consultation.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only rate your own legal responses")
    feedback = db.scalar(select(Feedback).where(Feedback.response_id == response_id, Feedback.user_id == user.id))
    if feedback:
        feedback.rating = payload.rating
    else:
        db.add(Feedback(response_id=response_id, user_id=user.id, rating=payload.rating))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/admin/statistics")
def statistics(_: AdminUser, db: DbSession) -> dict:
    today = datetime.now(timezone.utc).date()
    month_start = today.replace(day=1)
    consultation_count = db.scalar(select(func.count()).select_from(Consultation)) or 0
    return {
        "consultations_today": db.scalar(select(func.count()).select_from(Consultation).where(Consultation.created_at >= datetime.combine(today, time.min, tzinfo=timezone.utc))) or 0,
        "consultations_month": db.scalar(select(func.count()).select_from(Consultation).where(Consultation.created_at >= datetime.combine(month_start, time.min, tzinfo=timezone.utc))) or 0,
        "agent_lookups_month": db.scalar(select(func.count()).select_from(AgentLookup).where(AgentLookup.created_at >= datetime.combine(month_start, time.min, tzinfo=timezone.utc))) or 0,
        "consultations_total": consultation_count,
        "consultations_by_category": dict(db.execute(select(LegalResponse.category, func.count()).group_by(LegalResponse.category)).all()),
        "average_feedback_rating": db.scalar(select(func.avg(Feedback.rating)))
    }

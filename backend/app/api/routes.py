from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select

from app.api.deps import AdminUser, CurrentUser, DbSession, OptionalUser
from app.core.security import create_access_token, hash_password, verify_password
from app.models.domain import AgentLookup, Conversation, Message, MessageFeedback, MessageRole, User
from app.schemas.api import (AdminUserUpdate, AgentPublic, AgentSearchResponse, OfficialSourcePublic, LoginRequest, ProfileUpdate, RegisterRequest, TokenResponse, UserPublic)
from app.services.agents_registry import EmptyAgentQuery, search_agents

MEXICO_CITY = ZoneInfo("America/Mexico_City")  # the product's calendar: "today" and "this month" follow the user's day

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


@router.get("/agents/search", response_model=AgentSearchResponse)
def search_authorized_agents(
    user: OptionalUser, db: DbSession, q: Annotated[str, Query(min_length=2, max_length=100)]
) -> AgentSearchResponse:
    try:
        search = search_agents(db, q)
    except EmptyAgentQuery as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Escribe una placa o un nombre") from exc
    top_agent_id = search.matches[0].agent.id if search.matches else None
    db.add(AgentLookup(user_id=user.id if user else None, agent_id=top_agent_id))
    db.commit()
    return AgentSearchResponse(
        query=q,
        matched_by=search.matched_by,
        results=[AgentPublic.model_validate(match.agent) for match in search.matches],
        source=OfficialSourcePublic.model_validate(search.source) if search.source else None,
    )


@router.get("/admin/statistics")
def statistics(_: AdminUser, db: DbSession) -> dict:
    now = datetime.now(MEXICO_CITY)
    day_start = datetime.combine(now.date(), time.min, tzinfo=MEXICO_CITY)
    month_start = day_start.replace(day=1)

    def user_messages(since: datetime | None = None) -> int:
        query = select(func.count()).select_from(Message).where(Message.role == MessageRole.USER)
        if since is not None:
            query = query.where(Message.created_at >= since)
        return db.scalar(query) or 0

    def feedback(value: int) -> int:
        return db.scalar(select(func.count()).select_from(MessageFeedback).where(MessageFeedback.value == value)) or 0

    positive, negative = feedback(1), feedback(-1)
    return {
        "messages_today": user_messages(day_start),
        "messages_month": user_messages(month_start),
        "messages_total": user_messages(),
        "conversations_total": db.scalar(select(func.count()).select_from(Conversation)) or 0,
        "agent_lookups_month": db.scalar(select(func.count()).select_from(AgentLookup).where(AgentLookup.created_at >= month_start)) or 0,
        "feedback_positive": positive,
        "feedback_negative": negative,
        "feedback_positive_rate": positive / (positive + negative) if positive + negative else None,
    }

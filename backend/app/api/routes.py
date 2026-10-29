from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select

from app.api.admin import router as admin_router
from app.api.conversations import router as conversations_router
from app.api.deps import CurrentUser, DbSession, OptionalUser
from app.core.config import get_settings
from app.core.rate_limit import limiter, rate_limit, too_many
from app.core.security import create_access_token, hash_password, verify_password
from app.models.domain import AgentLookup, User
from app.schemas.api import (AgentPublic, AgentSearchResponse, OfficialSourcePublic, GoogleLoginRequest, LoginRequest, ProfileUpdate, RegisterRequest, TokenResponse, UserPublic)
from app.services.agents_registry import EmptyAgentQuery, search_agents
from app.services.google_auth import InvalidGoogleToken, sign_in_with_google, verify_google_credential

router = APIRouter(prefix="/api/v1")
router.include_router(conversations_router)
router.include_router(admin_router)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(rate_limit("register", 5, 3600))])
def register(payload: RegisterRequest, db: DbSession) -> User:
    exists = db.scalar(select(User.id).where(User.email == str(payload.email)))
    if exists:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(first_name=payload.first_name, last_name=payload.last_name, email=str(payload.email), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse, dependencies=[Depends(rate_limit("login", 10, 60))])
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    # Per account as well as per address: guessing one password from many addresses is the usual way past the IP limit.
    wait = limiter.hit("login-account", str(payload.email).lower(), 10, 900)
    if wait is not None:
        raise too_many(wait)
    user = db.scalar(select(User).where(User.email == str(payload.email)))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(str(user.id), user.token_version), user=user)


def google_verifier():
    """Seam for tests: the real one calls Google's public keys."""
    return verify_google_credential


@router.post("/auth/google", response_model=TokenResponse, dependencies=[Depends(rate_limit("google", 20, 60))])
def login_with_google(payload: GoogleLoginRequest, db: DbSession, verifier=Depends(google_verifier)) -> TokenResponse:
    client_id = get_settings().google_client_id
    if not client_id:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "El inicio de sesión con Google no está disponible")
    try:
        identity = verifier(payload.credential, client_id)
    except InvalidGoogleToken:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No pudimos verificar tu cuenta de Google")
    user = sign_in_with_google(db, identity)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenResponse(access_token=create_access_token(str(user.id), user.token_version), user=user)


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
        if email != user.email:
            user.email_verified_at = None  # a new address has not been proven yet
        user.email = email
    for field in ("first_name", "last_name"):
        if field in values:
            setattr(user, field, values[field])
    if password := values.get("password"):
        user.password_hash = hash_password(password)
    db.commit()
    db.refresh(user)
    return user


@router.get("/agents/search", response_model=AgentSearchResponse, dependencies=[Depends(rate_limit("agents-search", 30, 60))])
def search_authorized_agents(
    user: OptionalUser, db: DbSession, q: Annotated[str, Query(min_length=2, max_length=100)]
) -> AgentSearchResponse:
    try:
        search = search_agents(db, q)
    except EmptyAgentQuery as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Escribe una placa o un nombre") from exc
    # Only an exact plate match identifies the agent; a fuzzy name match is a guess and would be logged as a fact.
    top_agent_id = search.matches[0].agent.id if search.matches and search.matched_by == "plate" else None
    db.add(AgentLookup(user_id=user.id if user else None, agent_id=top_agent_id))
    db.commit()
    return AgentSearchResponse(
        query=q,
        matched_by=search.matched_by,
        results=[AgentPublic.model_validate(match.agent) for match in search.matches],
        source=OfficialSourcePublic.model_validate(search.source) if search.source else None,
    )

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.api.admin import router as admin_router
from app.api.conversations import router as conversations_router
from app.api.deps import CurrentUser, DbSession, OptionalUser
from app.core.config import TERMS_VERSION, get_settings
from app.core.rate_limit import limiter, rate_limit, too_many
from app.core.security import create_access_token, hash_password, verify_password
from app.models.domain import AgentLookup, User
from app.services.email_tokens import hash_token
from app.services.mailer import Mailer, get_mailer
from app.schemas.api import (AgentPublic, AgentSearchResponse, ForgotPasswordRequest, MessageResponse, ResetPasswordRequest, VerifyEmailRequest, OfficialSourcePublic, GoogleLoginRequest, LoginRequest, ProfileUpdate, RegisterRequest, TokenResponse, UserPublic)
from app.services.accounts import CurrentPasswordRequired, EmailTaken, apply_profile_update, queue_password_reset_email, queue_verification_email, reset_password, verify_email
from app.services.agents_registry import EmptyAgentQuery, search_agents
from app.services.google_auth import InvalidGoogleToken, sign_in_with_google, verify_google_credential

MailerDep = Annotated[Mailer, Depends(get_mailer)]

router = APIRouter(prefix="/api/v1")
router.include_router(conversations_router)
router.include_router(admin_router)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}



@router.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(rate_limit("register", 5, 3600))])
def register(payload: RegisterRequest, db: DbSession, background: BackgroundTasks, mailer: MailerDep) -> User:
    exists = db.scalar(select(User.id).where(func.lower(User.email) == str(payload.email)))
    if exists:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(first_name=payload.first_name, last_name=payload.last_name, email=str(payload.email), password_hash=hash_password(payload.password),
                terms_accepted_at=datetime.now(timezone.utc), terms_version=TERMS_VERSION)
    db.add(user)
    db.commit()
    db.refresh(user)
    queue_verification_email(db, user, background, mailer)
    return user


@router.post("/auth/login", response_model=TokenResponse, dependencies=[Depends(rate_limit("login", 10, 60))])
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    # Per account as well as per address: guessing one password from many addresses is the usual way past the IP limit.
    wait = limiter.hit("login-account", str(payload.email).lower(), 10, 900)
    if wait is not None:
        raise too_many(wait)
    user = db.scalar(select(User).where(func.lower(User.email) == str(payload.email)))
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


def _limit(bucket: str, key: str, limit: int, window: float) -> None:
    wait = limiter.hit(bucket, key, limit, window)
    if wait is not None:
        raise too_many(wait)


_BAD_TOKEN = "El enlace no es válido o ya venció"


@router.post("/auth/verify-email", response_model=MessageResponse, dependencies=[Depends(rate_limit("verify-email", 10, 60))])
def verify_email_endpoint(payload: VerifyEmailRequest, db: DbSession) -> MessageResponse:
    _limit("verify-email-token", hash_token(payload.token), 5, 900)
    if not verify_email(db, payload.token):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, _BAD_TOKEN)
    return MessageResponse(detail="Correo verificado")


@router.post("/auth/resend-verification", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED,
             dependencies=[Depends(rate_limit("resend-verification", 10, 3600))])
def resend_verification(user: CurrentUser, db: DbSession, background: BackgroundTasks, mailer: MailerDep) -> MessageResponse:
    _limit("resend-verification-user", str(user.id), 5, 3600)
    if user.email_verified_at is None:
        queue_verification_email(db, user, background, mailer)
    return MessageResponse(detail="Si tu correo aún no está verificado, te enviamos un enlace")


@router.post("/auth/forgot-password", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED,
             dependencies=[Depends(rate_limit("forgot-password", 10, 3600))])
def forgot_password(payload: ForgotPasswordRequest, db: DbSession, background: BackgroundTasks, mailer: MailerDep) -> MessageResponse:
    email = str(payload.email)
    _limit("forgot-password-email", email, 3, 3600)
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if user is not None and user.is_active:
        queue_password_reset_email(db, user, background, mailer)
    return MessageResponse(detail="Si el correo está registrado, te enviamos instrucciones")


@router.post("/auth/reset-password", response_model=MessageResponse, dependencies=[Depends(rate_limit("reset-password", 10, 60))])
def reset_password_endpoint(payload: ResetPasswordRequest, db: DbSession) -> MessageResponse:
    _limit("reset-password-token", hash_token(payload.token), 5, 900)
    if not reset_password(db, payload.token, payload.password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, _BAD_TOKEN)
    return MessageResponse(detail="Contraseña actualizada")


@router.get("/users/me", response_model=UserPublic)
def read_profile(user: CurrentUser) -> User:
    return user


@router.patch("/users/me", response_model=UserPublic)
def update_profile(payload: ProfileUpdate, user: CurrentUser, db: DbSession, background: BackgroundTasks, mailer: MailerDep) -> User:
    old_email = user.email
    try:
        updated = apply_profile_update(db, user, payload.model_dump(exclude_unset=True))
        if updated.email != old_email:
            queue_verification_email(db, updated, background, mailer)  # to the new address
        return updated
    except CurrentPasswordRequired as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    except EmailTaken as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email is already registered") from exc


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

"""One-time e-mail tokens (address verification, password reset). Only the sha256 of a token is stored."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.domain import EmailToken, EmailTokenPurpose, User

LIFETIME = {EmailTokenPurpose.VERIFY: timedelta(hours=24), EmailTokenPurpose.RESET: timedelta(hours=1)}


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def issue_token(db: Session, user: User, purpose: EmailTokenPurpose) -> tuple[str, str]:
    """Create a token (earlier unused ones of the same purpose stop working). Returns (raw, hash); commits."""
    now = _now()
    db.execute(
        update(EmailToken)
        .where(EmailToken.user_id == user.id, EmailToken.purpose == purpose, EmailToken.used_at.is_(None))
        .values(used_at=now)
    )
    raw = secrets.token_urlsafe(32)
    digest = hash_token(raw)
    db.add(EmailToken(user_id=user.id, purpose=purpose, token_hash=digest, expires_at=now + LIFETIME[purpose]))
    db.commit()
    return raw, digest


def redeem_token(db: Session, raw: str, purpose: EmailTokenPurpose) -> User | None:
    """Mark the token used and return its (active) user, or None if unknown, expired, used or of another purpose.

    Does not commit: the caller applies its change and commits in the same transaction.
    """
    digest = hash_token(raw)
    row = db.scalar(
        select(EmailToken).where(EmailToken.token_hash == digest, EmailToken.purpose == purpose).with_for_update()
    )
    if row is None or not hmac.compare_digest(row.token_hash, digest):
        return None
    if row.used_at is not None or row.expires_at <= _now():
        return None
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        return None
    row.used_at = _now()
    return user


def invalidate_tokens(db: Session, user: User, purpose: EmailTokenPurpose) -> None:
    db.execute(
        update(EmailToken)
        .where(EmailToken.user_id == user.id, EmailToken.purpose == purpose, EmailToken.used_at.is_(None))
        .values(used_at=_now())
    )

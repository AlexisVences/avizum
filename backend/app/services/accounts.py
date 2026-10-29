from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.domain import EmailTokenPurpose, User
from app.services import mailer as mail
from app.services.email_tokens import invalidate_tokens, issue_token, redeem_token


def queue_verification_email(db: Session, user: User, background: BackgroundTasks, sender: mail.Mailer) -> None:
    """Issue a verification token now and queue its delivery after the response."""
    raw, digest = issue_token(db, user, EmailTokenPurpose.VERIFY)
    subject, html, text = mail.verification_message(get_settings().frontend_url, raw, user.first_name)
    background.add_task(mail.deliver, sender, user.email, subject, html, text, f"verify-{digest[:32]}")


def queue_password_reset_email(db: Session, user: User, background: BackgroundTasks, sender: mail.Mailer) -> None:
    """Reset link for accounts with a password; an explanation for Google-only accounts (no token is created)."""
    if user.password_hash is None:
        subject, html, text = mail.google_account_message(user.first_name)
        key = f"google-only-{user.id}-{datetime.now(timezone.utc):%Y%m%d%H%M%S%f}"
    else:
        raw, digest = issue_token(db, user, EmailTokenPurpose.RESET)
        subject, html, text = mail.reset_message(get_settings().frontend_url, raw, user.first_name)
        key = f"reset-{digest[:32]}"
    background.add_task(mail.deliver, sender, user.email, subject, html, text, key)


def verify_email(db: Session, raw_token: str) -> bool:
    user = redeem_token(db, raw_token, EmailTokenPurpose.VERIFY)
    if user is None:
        return False
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(timezone.utc)
    db.commit()
    return True


def reset_password(db: Session, raw_token: str, new_password: str) -> bool:
    user = redeem_token(db, raw_token, EmailTokenPurpose.RESET)
    if user is None:
        return False
    user.password_hash = hash_password(new_password)
    user.token_version += 1
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(timezone.utc)  # the reset link reached the mailbox
    invalidate_tokens(db, user, EmailTokenPurpose.RESET)
    db.commit()
    return True


class CurrentPasswordRequired(Exception):
    """The change needs proof of the current password and it was missing, wrong, or does not exist."""


class EmailTaken(Exception):
    pass


def apply_profile_update(db: Session, user: User, values: dict) -> User:
    """Apply a profile change. Emails arrive already normalised (lowercase, trimmed).

    Changing the email or the password needs the current password. An account that only signs in with
    Google has no password: it may set a first one (the bearer token is its proof), but may not change its
    email, because nothing else proves who is asking. Setting a password revokes every issued token.
    """
    new_email = values.get("email")
    email_changes = new_email is not None and new_email != user.email.lower()
    new_password = values.get("password")

    if email_changes or new_password:
        has_password = user.password_hash is not None
        if has_password:
            current = values.get("current_password")
            if not current or not verify_password(current, user.password_hash):
                raise CurrentPasswordRequired("Current password is required and must be correct")
        elif email_changes:
            raise CurrentPasswordRequired("Set a password before changing your email")

    if email_changes:
        taken = db.scalar(select(User.id).where(func.lower(User.email) == new_email, User.id != user.id))
        if taken:
            raise EmailTaken()
        user.email = new_email
        user.email_verified_at = None  # a new address has not been proven yet
    for field in ("first_name", "last_name"):
        if field in values:
            setattr(user, field, values[field])
    if new_password:
        user.password_hash = hash_password(new_password)
        user.token_version += 1
    db.commit()
    db.refresh(user)
    return user

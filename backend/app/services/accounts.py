from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.domain import User


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

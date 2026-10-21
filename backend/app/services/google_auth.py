"""Sign in with Google: verify the ID token the browser got from Google Identity Services.

The frontend never sends a Google identity as plain data; it sends the signed token, and the signature, issuer,
audience (this app's client ID) and expiry are checked here against Google's published keys.
"""
from dataclasses import dataclass

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class InvalidGoogleToken(Exception):
    pass


@dataclass(frozen=True)
class GoogleIdentity:
    sub: str
    email: str
    first_name: str
    last_name: str


def verify_google_credential(credential: str, client_id: str) -> GoogleIdentity:
    try:
        info = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id, clock_skew_in_seconds=10)
    except Exception as exc:  # google-auth raises ValueError, GoogleAuthError or transport errors
        raise InvalidGoogleToken(str(exc)) from exc
    if info.get("iss") not in ISSUERS or not info.get("email") or info.get("email_verified") is not True:
        raise InvalidGoogleToken("the token has no verified email")
    email = str(info["email"]).lower()
    first = (info.get("given_name") or info.get("name") or email.split("@")[0])[:100]
    return GoogleIdentity(sub=str(info["sub"]), email=email, first_name=first, last_name=(info.get("family_name") or "")[:100])


def sign_in_with_google(db, identity: GoogleIdentity):
    """Return the user for this Google identity, creating or linking the account. Returns None if it is disabled."""
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.models.domain import User

    now = datetime.now(timezone.utc)
    user = db.scalar(select(User).where(User.google_sub == identity.sub))
    if user is None:
        user = db.scalar(select(User).where(User.email == identity.email))
        if user is not None:
            if user.email_verified_at is None:
                # Someone may have registered this address with a password without proving they own it. Whoever
                # owns the inbox is now signing in through Google, so that password must stop working.
                user.password_hash = None
                user.token_version += 1  # and any session that password already opened
            user.google_sub = identity.sub
            user.email_verified_at = user.email_verified_at or now
        else:
            user = User(first_name=identity.first_name, last_name=identity.last_name, email=identity.email,
                        password_hash=None, google_sub=identity.sub, email_verified_at=now)
            db.add(user)
        db.commit()
        db.refresh(user)
    return user if user.is_active else None

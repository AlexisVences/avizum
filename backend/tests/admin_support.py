from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token
from app.models.domain import User, UserRole


def make_user(
    factory: sessionmaker,
    *,
    email: str,
    role: UserRole = UserRole.USER,
    is_active: bool = True,
    verified: bool = True,
) -> tuple[User, dict[str, str]]:
    """Create a user directly in the database and return it with a Bearer header for it."""
    with factory() as db:
        user = User(
            first_name="Test",
            last_name="User",
            email=email,
            password_hash=None,
            role=role,
            is_active=is_active,
            email_verified_at=datetime.now(timezone.utc) if verified else None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user, {"Authorization": f"Bearer {create_access_token(str(user.id), user.token_version)}"}

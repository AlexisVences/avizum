"""Grant an existing user the administrator role; run only with database-admin access."""
import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.domain import User, UserRole


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == args.username))
        if user is None:
            raise SystemExit(f"No user exists with username {args.username!r}")
        user.role = UserRole.ADMIN
        db.commit()
    print(f"Promoted {args.username!r} to admin.")


if __name__ == "__main__":
    main()

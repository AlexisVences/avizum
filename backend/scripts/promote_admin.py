"""Grant an existing user the administrator role; run only with database-admin access."""
import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.domain import User, UserRole


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.email))
        if user is None:
            raise SystemExit(f"No user exists with email {args.email!r}")
        user.role = UserRole.ADMIN
        db.commit()
    print(f"Promoted {args.email!r} to admin.")


if __name__ == "__main__":
    main()

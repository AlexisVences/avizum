"""users.email: lowercase existing addresses and add a unique index on lower(email)

Revision ID: 20261029_14
Revises: 20261025_13
Create Date: 2026-10-29
"""
from alembic import op

revision = "20261029_14"
down_revision = "20261025_13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    clashes = bind.exec_driver_sql(
        "SELECT lower(btrim(email)) AS e, array_agg(id ORDER BY id) AS ids FROM users "
        "GROUP BY lower(btrim(email)) HAVING count(*) > 1"
    ).fetchall()
    if clashes:
        detail = "; ".join(f"{row.e} -> user ids {list(row.ids)}" for row in clashes)
        raise RuntimeError(
            "Cannot add the case-insensitive unique index on users.email: these addresses exist more than "
            f"once when case and surrounding spaces are ignored ({detail}). Accounts are never merged "
            "automatically; resolve them by hand (delete or rename one of each pair) and run the migration again."
        )
    # The application now always stores and looks up lowercase addresses.
    op.execute("UPDATE users SET email = lower(btrim(email)) WHERE email <> lower(btrim(email))")
    op.execute("CREATE UNIQUE INDEX ix_users_email_lower ON users (lower(email))")


def downgrade() -> None:
    # Lowercased addresses are left as they are: the original casing is not recoverable.
    op.execute("DROP INDEX ix_users_email_lower")

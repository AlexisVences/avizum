"""Load the authorized-agents CSV registry into the database; safe to re-run."""
import argparse
import csv
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal
from app.models.domain import AuthorizedAgent

DEFAULT_CSV = Path(__file__).resolve().parents[2] / "data" / "agents" / "agentes_procesados.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", nargs="?", default=DEFAULT_CSV, type=Path)
    args = parser.parse_args()

    with args.csv_path.open(newline="", encoding="utf-8") as f:
        rows = [
            {"plate": row["placa"].strip(), "name": row["nombre_completo"].strip()}
            for row in csv.DictReader(f)
            if row["placa"].strip()
        ]
    if not rows:
        raise SystemExit(f"No rows found in {args.csv_path}")

    with SessionLocal() as db:
        stmt = insert(AuthorizedAgent).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[AuthorizedAgent.plate],
            set_={"name": stmt.excluded.name},
        )
        db.execute(stmt)
        db.commit()
    print(f"Seeded {len(rows)} authorized agents from {args.csv_path}.")


if __name__ == "__main__":
    main()

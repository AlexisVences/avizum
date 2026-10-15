from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.domain import EMBEDDING_DIMENSIONS, LegalChunk, LegalSanction, OfficialSource, SanctionStatus

HASH = "a" * 64


def _chunk(db) -> LegalChunk:
    source = OfficialSource(slug="reglamento-transito", title="Reglamento", kind="reglamento", url="https://x.mx/r.pdf", sha256="b" * 64)
    db.add(source)
    db.flush()
    chunk = LegalChunk(
        source_id=source.id, article="37", fraction="II", heading_path="Art. 37", text="texto", page_start=1,
        page_end=1, token_count=1, embedding=[0.0] * EMBEDDING_DIMENSIONS,
    )
    db.add(chunk)
    db.flush()
    return chunk


def _row(chunk_id: int, ordinal: int = 0, **overrides) -> LegalSanction:
    values = dict(
        chunk_id=chunk_id, ordinal=ordinal, source_slug="reglamento-transito", article="37", fraction="II", inciso="b",
        conduct_text="Asegurarse que todos los pasajeros utilicen el cinturón", clause_text="5, 7 o 10 veces la UMA",
        uma_min=Decimal("5"), uma_mid=Decimal("7"), uma_max=Decimal("10"), points_license=1,
        chunk_hash=HASH, extractor_version="test",
    )
    values.update(overrides)
    return LegalSanction(**values)


def test_a_new_row_is_pending_so_it_is_not_served_until_a_person_verifies_it(client):
    _, factory = client
    with factory() as db:
        chunk = _chunk(db)
        db.add(_row(chunk.id))
        db.commit()
        saved = db.scalars(select(LegalSanction)).one()
        assert saved.status is SanctionStatus.PENDING
        assert saved.reviewed_by is None and saved.reviewed_at is None
        assert saved.uma_mid == Decimal("7.00")


@pytest.mark.parametrize(
    "overrides",
    [
        {"uma_min": Decimal("10"), "uma_mid": Decimal("7"), "uma_max": Decimal("5")},  # not ascending
        {"uma_min": None, "uma_mid": Decimal("7"), "uma_max": None},  # a middle value without a minimum
        {"uma_min": Decimal("0"), "uma_mid": None, "uma_max": None},  # a fine of zero UMA
        {"points_license": -1},
        {"chunk_hash": "short"},
    ],
)
def test_the_database_rejects_rows_that_cannot_be_a_real_sanction(client, overrides):
    _, factory = client
    with factory() as db:
        chunk = _chunk(db)
        db.add(_row(chunk.id, **overrides))
        with pytest.raises(IntegrityError):
            db.commit()


def test_a_fixed_fine_and_a_sanction_without_uma_are_valid(client):
    _, factory = client
    with factory() as db:
        chunk = _chunk(db)
        db.add_all([
            _row(chunk.id, 0, uma_mid=None, uma_max=None),  # one fixed amount
            _row(chunk.id, 1, uma_min=None, uma_mid=None, uma_max=None, points_license=None,
                 other_consequences="remisión del vehículo al depósito"),
        ])
        db.commit()
        assert len(db.scalars(select(LegalSanction)).all()) == 2


def test_one_chunk_cannot_have_two_rows_at_the_same_position(client):
    _, factory = client
    with factory() as db:
        chunk = _chunk(db)
        db.add_all([_row(chunk.id, 0), _row(chunk.id, 0, inciso="c")])
        with pytest.raises(IntegrityError):
            db.commit()


def test_rows_go_away_with_their_chunk(client):
    _, factory = client
    with factory() as db:
        chunk = _chunk(db)
        db.add(_row(chunk.id))
        db.commit()
        db.delete(chunk)
        db.commit()
        assert db.scalars(select(LegalSanction)).all() == []

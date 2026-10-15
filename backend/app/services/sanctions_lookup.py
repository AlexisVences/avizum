"""Which structured sanctions the agent may serve.

Only rows a person verified, whose `chunk_hash` still equals the hash of the chunk text in the database, and whose
source is the current version. Anything else (pending, rejected, stale, edited text) is invisible: the agent then
falls back to reading the prose, exactly as it did before the table existed.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.domain import LegalChunk, LegalSanction, OfficialSource, SanctionStatus


def verified_by_chunk(db: Session, chunk_ids: list[int]) -> dict[int, list[LegalSanction]]:
    if not chunk_ids:
        return {}
    digest = func.encode(func.sha256(func.convert_to(LegalChunk.text, "UTF8")), "hex")
    rows = db.scalars(
        select(LegalSanction)
        .join(LegalChunk, LegalChunk.id == LegalSanction.chunk_id)
        .join(OfficialSource, OfficialSource.id == LegalChunk.source_id)
        .where(
            LegalSanction.chunk_id.in_(chunk_ids),
            LegalSanction.status == SanctionStatus.VERIFIED,
            OfficialSource.is_current,
            LegalSanction.chunk_hash == digest,
        )
        .order_by(LegalSanction.chunk_id, LegalSanction.ordinal)
    ).all()
    grouped: dict[int, list[LegalSanction]] = {}
    for row in rows:
        grouped.setdefault(row.chunk_id, []).append(row)
    return grouped

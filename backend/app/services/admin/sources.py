from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.domain import LegalChunk, LegalSanction, OfficialSource, SanctionStatus
from app.schemas.admin import SourceRow
from app.services.chat_limits import MEXICO_CITY

REVIEW_AFTER_DAYS = 365


def list_sources(db: Session, *, today: date | None = None) -> list[SourceRow]:
    """One row per source whose current version exists; chunk_count is that version's."""
    today = today or datetime.now(MEXICO_CITY).date()
    chunks = (
        select(LegalChunk.source_id, func.count().label("n")).group_by(LegalChunk.source_id)
        .subquery()
    )
    versions = (
        select(OfficialSource.slug, func.count().label("n")).group_by(OfficialSource.slug)
        .subquery()
    )
    query = (
        select(OfficialSource, func.coalesce(chunks.c.n, 0), versions.c.n)
        .outerjoin(chunks, chunks.c.source_id == OfficialSource.id)
        .join(versions, versions.c.slug == OfficialSource.slug)
        .where(OfficialSource.is_current.is_(True))
        .order_by(OfficialSource.kind, OfficialSource.title, OfficialSource.slug)
    )
    rows = []
    for source, chunk_count, version_count in db.execute(query):
        retrieved = source.retrieved_at.astimezone(MEXICO_CITY).date()
        due = retrieved + timedelta(days=REVIEW_AFTER_DAYS) < today
        rows.append(SourceRow(
            slug=source.slug, title=source.title, kind=source.kind, url=source.url,
            last_reform_date=source.last_reform_date, retrieved_at=source.retrieved_at,
            chunk_count=chunk_count, versions=version_count, review_due=due,
            review_due_since=retrieved + timedelta(days=REVIEW_AFTER_DAYS + 1) if due else None,
        ))
    return rows


def pending_sanctions(db: Session) -> int:
    return db.scalar(
        select(func.count()).select_from(LegalSanction)
        .where(LegalSanction.status == SanctionStatus.PENDING)
    ) or 0

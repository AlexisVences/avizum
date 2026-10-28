from collections.abc import Callable

from sqlalchemy.orm import Session

from app.schemas.admin import AttentionItem
from app.services.admin.review import count_unreviewed
from app.services.admin.sources import list_sources, pending_sanctions


def _review_queue(db: Session) -> list[AttentionItem]:
    count = count_unreviewed(db)
    if not count:
        return []
    return [AttentionItem(kind="review", label="respuestas por revisar", count=count,
                          href="/admin/calidad")]


def _sources_due(db: Session) -> list[AttentionItem]:
    count = sum(1 for row in list_sources(db) if row.review_due)
    if not count:
        return []
    return [AttentionItem(kind="sources", label="fuentes por revisar este año", count=count,
                          href="/admin/fuentes")]


def _pending_sanctions(db: Session) -> list[AttentionItem]:
    count = pending_sanctions(db)
    if not count:
        return []
    return [AttentionItem(kind="sanctions", label="filas de sanciones sin revisar", count=count,
                          href="/admin/fuentes")]


# Each provider returns the items it wants to surface; later phases append theirs here.
PROVIDERS: list[Callable[[Session], list[AttentionItem]]] = [
    _review_queue, _sources_due, _pending_sanctions,
]


def collect_attention(db: Session) -> list[AttentionItem]:
    return [item for provider in PROVIDERS for item in provider(db)]

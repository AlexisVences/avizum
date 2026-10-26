from collections.abc import Callable

from sqlalchemy.orm import Session

from app.schemas.admin import AttentionItem
from app.services.admin.review import count_unreviewed


def _review_queue(db: Session) -> list[AttentionItem]:
    count = count_unreviewed(db)
    if not count:
        return []
    return [AttentionItem(kind="review", label="respuestas por revisar", count=count,
                          href="/admin/calidad")]


# Each provider returns the items it wants to surface; later phases append theirs here.
PROVIDERS: list[Callable[[Session], list[AttentionItem]]] = [_review_queue]


def collect_attention(db: Session) -> list[AttentionItem]:
    return [item for provider in PROVIDERS for item in provider(db)]

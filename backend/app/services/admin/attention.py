from collections.abc import Callable

from sqlalchemy.orm import Session

from app.schemas.admin import AttentionItem

# Each provider returns the items it wants to surface; later phases append theirs here.
PROVIDERS: list[Callable[[Session], list[AttentionItem]]] = []


def collect_attention(db: Session) -> list[AttentionItem]:
    return [item for provider in PROVIDERS for item in provider(db)]

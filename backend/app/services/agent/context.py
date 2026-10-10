"""Per-turn state shared by the agent's tools.

LangChain passes this object to every tool through `ToolRuntime.context`; the model never sees it, so it cannot
invent a database session or a user id. The citation registry is what turns the fragments the tools returned into
the `[n]` markers the model writes and the links the user sees.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

from langchain_core.embeddings import Embeddings
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.services.retrieval import SearchHit


@dataclass(frozen=True)
class Citation:
    n: int
    chunk_id: int
    source_slug: str
    source_title: str
    article: str
    fraction: str | None
    page: int | None  # None for a whole source (e.g. the agents acuerdo)
    url: str  # the official PDF opened at the page of the fragment


class CitationRegistry:
    """Numbers fragments 1, 2, 3… in the order a turn first returns them; a fragment keeps its number."""

    def __init__(self) -> None:
        self._by_chunk: dict[int, Citation] = {}

    def register(self, hit: SearchHit) -> Citation:
        existing = self._by_chunk.get(hit.chunk_id)
        if existing:
            return existing
        url = f"{hit.source_url}#page={hit.page_start}" if hit.source_url.startswith("http") else hit.source_url
        citation = Citation(
            n=len(self._by_chunk) + 1, chunk_id=hit.chunk_id, source_slug=hit.source_slug, source_title=hit.source_title,
            article=hit.article, fraction=hit.fraction, page=hit.page_start, url=url,
        )
        self._by_chunk[hit.chunk_id] = citation
        return citation

    def register_source(self, *, source_id: int, slug: str, title: str, url: str) -> Citation:
        """A citable whole document (the agents acuerdo): there is no article or page to point at."""
        key = -source_id  # chunk ids are positive, so a source never collides with a fragment
        existing = self._by_chunk.get(key)
        if existing:
            return existing
        citation = Citation(
            n=len(self._by_chunk) + 1, chunk_id=key, source_slug=slug, source_title=title, article="", fraction=None,
            page=None, url=url,
        )
        self._by_chunk[key] = citation
        return citation

    def get(self, n: int) -> Citation | None:
        return next((c for c in self._by_chunk.values() if c.n == n), None)

    def all(self) -> list[Citation]:
        return sorted(self._by_chunk.values(), key=lambda c: c.n)


@dataclass
class AgentContext:
    db: Session
    user_id: int | None
    embeddings: Embeddings
    user_message: str  # the user's own words: the second phrasing of every legislation search
    citations: CitationRegistry = field(default_factory=CitationRegistry)
    settings: Settings = field(default_factory=get_settings)
    today: date | None = None  # injectable for tests; defaults to the current date in Mexico City
    searched: list[str] = field(default_factory=list)  # legislation queries already run this turn

    @property
    def searches_run(self) -> int:
        return len(self.searched)

    def current_date(self) -> date:
        return self.today or datetime.now(ZoneInfo("America/Mexico_City")).date()

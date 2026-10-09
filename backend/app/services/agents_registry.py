"""Authorized-agents registry: normalization and lookup against the official Gaceta list."""
import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.models.domain import AuthorizedAgent, OfficialSource

AGENTS_SOURCE_SLUG = "acuerdo-agentes-transito"
PLATE_PATTERN = re.compile(r"\d+")
# greatest(similarity, word_similarity) >= 0.45 keeps typos ("zabala tobar karla" = 0.50) and
# partial names ("karla zavala" = 0.67) while dropping unrelated names ("juan perez" ≈ 0.09).
NAME_MATCH_THRESHOLD = 0.45
MAX_RESULTS = 10


@dataclass(frozen=True)
class AgentMatch:
    agent: AuthorizedAgent
    score: float


class EmptyAgentQuery(ValueError):
    pass


@dataclass(frozen=True)
class AgentSearch:
    matches: list[AgentMatch]
    source: OfficialSource | None
    matched_by: Literal["plate", "name"]


def normalize_name(value: str) -> str:
    """Lowercase, strip accents (ñ → n) and punctuation, collapse whitespace."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    letters_only = re.sub(r"[^a-z\s]", " ", without_accents.lower())
    return " ".join(letters_only.split())


def normalize_plate(value: str) -> str:
    return re.sub(r"[\s\-]", "", value).upper()


def current_agents_source(db: Session) -> OfficialSource | None:
    return db.scalar(
        select(OfficialSource).where(OfficialSource.slug == AGENTS_SOURCE_SLUG, OfficialSource.is_current)
    )


def imported_agents_source(db: Session) -> OfficialSource | None:
    """The current source, only if its agents were actually imported (else the registry is unavailable)."""
    source = current_agents_source(db)
    if source is None:
        return None
    imported = db.scalar(select(exists().where(AuthorizedAgent.source_id == source.id)))
    return source if imported else None


def search_agents(db: Session, query: str) -> AgentSearch:
    plate = normalize_plate(query)
    is_plate = bool(PLATE_PATTERN.fullmatch(plate))
    name = normalize_name(query)
    if not is_plate and not name:
        raise EmptyAgentQuery("La consulta no contiene una placa ni un nombre")
    source = imported_agents_source(db)
    if source is None:
        return AgentSearch([], None, "plate" if is_plate else "name")
    if is_plate:
        agents = db.scalars(
            select(AuthorizedAgent)
            .where(AuthorizedAgent.plate == plate, AuthorizedAgent.source_id == source.id)
            .order_by(AuthorizedAgent.authorization_type)
        ).all()
        return AgentSearch([AgentMatch(agent, 1.0) for agent in agents], source, "plate")

    score = func.greatest(
        func.similarity(AuthorizedAgent.name_search, name),
        func.word_similarity(name, AuthorizedAgent.name_search),
    )
    rows = db.execute(
        select(AuthorizedAgent, score)
        .where(score >= NAME_MATCH_THRESHOLD, AuthorizedAgent.source_id == source.id)
        .order_by(score.desc(), AuthorizedAgent.full_name)
        .limit(MAX_RESULTS)
    ).all()
    return AgentSearch([AgentMatch(agent, float(s)) for agent, s in rows], source, "name")

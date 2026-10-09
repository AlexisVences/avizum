from datetime import date

from sqlalchemy.orm import Session

from app.models.domain import AuthorizationType, AuthorizedAgent, OfficialSource
from app.services.agents_registry import AGENTS_SOURCE_SLUG, normalize_name


def add_agents_source(
    db: Session, *, slug: str = AGENTS_SOURCE_SLUG, sha256: str = "a" * 64, is_current: bool = True
) -> OfficialSource:
    source = OfficialSource(
        slug=slug,
        title="Acuerdo 30/2026 (GOCDMX 10-jun-2026)",
        kind="acuerdo",
        url="https://data.consejeria.cdmx.gob.mx/acuerdo-30-2026.pdf",
        sha256=sha256,
        last_reform_date=date(2026, 6, 10),
        is_current=is_current,
    )
    db.add(source)
    db.flush()
    return source


def add_agent(
    db: Session,
    source: OfficialSource,
    plate: str,
    full_name: str,
    authorization_type: AuthorizationType = AuthorizationType.VIA_PUBLICA,
) -> AuthorizedAgent:
    agent = AuthorizedAgent(
        plate=plate,
        full_name=full_name,
        name_search=normalize_name(full_name),
        authorization_type=authorization_type,
        source_id=source.id,
    )
    db.add(agent)
    db.flush()
    return agent

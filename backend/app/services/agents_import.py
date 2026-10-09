"""Replace the authorized-agents registry with the lists parsed from an official acuerdo."""
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.domain import AuthorizedAgent, OfficialSource
from app.services.acuerdo_parser import ParsedSection
from app.services.agents_registry import normalize_name, normalize_plate


def replace_agents(db: Session, source: OfficialSource, sections: list[ParsedSection]) -> dict[str, int]:
    """Delete every agent and insert the parsed lists in the caller's transaction (no commit)."""
    db.execute(delete(AuthorizedAgent))
    db.add_all(
        AuthorizedAgent(
            plate=normalize_plate(row.plate),
            full_name=row.full_name,
            name_search=normalize_name(row.full_name),
            authorization_type=section.authorization_type,
            source_id=source.id,
        )
        for section in sections
        for row in section.rows
    )
    db.flush()
    return {section.authorization_type.value: len(section.rows) for section in sections}

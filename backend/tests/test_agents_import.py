from sqlalchemy import select

from app.models.domain import AgentLookup, AuthorizationType, AuthorizedAgent
from app.services.acuerdo_parser import AgentRow, ParsedSection
from app.services.agents_import import replace_agents
from tests.factories import add_agent, add_agents_source

SECTIONS = [
    ParsedSection(AuthorizationType.VIA_PUBLICA, "PRIMERO", [
        AgentRow(1, "1168287", "ZAVALA TOVAR KARLA PAOLA"), AgentRow(2, "885312", "YAÑEZ GOMEZ VANESSA")]),
    ParsedSection(AuthorizationType.SISTEMAS_TECNOLOGICOS, "SEGUNDO", [AgentRow(1, "42006", "AGATON HERNANDEZ URIEL")]),
]


def test_replace_agents_swaps_the_whole_registry_and_keeps_lookup_history(client):
    _, factory = client
    with factory() as db:
        old_source = add_agents_source(db, sha256="a" * 64, is_current=False)
        old = add_agent(db, old_source, "999", "PEREZ LOPEZ ANA")
        db.add(AgentLookup(agent_id=old.id))
        new_source = add_agents_source(db, sha256="b" * 64)
        db.commit()

        counts = replace_agents(db, new_source, SECTIONS)
        db.commit()

        assert counts == {"via_publica": 2, "sistemas_tecnologicos": 1}
        agents = db.scalars(select(AuthorizedAgent).order_by(AuthorizedAgent.plate)).all()
        assert [(a.plate, a.authorization_type, a.source_id) for a in agents] == [
            ("1168287", AuthorizationType.VIA_PUBLICA, new_source.id),
            ("42006", AuthorizationType.SISTEMAS_TECNOLOGICOS, new_source.id),
            ("885312", AuthorizationType.VIA_PUBLICA, new_source.id),
        ]
        assert db.scalar(select(AuthorizedAgent.name_search).where(AuthorizedAgent.plate == "885312")) == "yanez gomez vanessa"
        lookup = db.scalar(select(AgentLookup))
        db.refresh(lookup)
        assert lookup.agent_id is None


def test_replace_agents_is_idempotent(client):
    _, factory = client
    with factory() as db:
        source = add_agents_source(db)
        db.commit()
        replace_agents(db, source, SECTIONS)
        db.commit()
        replace_agents(db, source, SECTIONS)
        db.commit()
        assert len(db.scalars(select(AuthorizedAgent)).all()) == 3

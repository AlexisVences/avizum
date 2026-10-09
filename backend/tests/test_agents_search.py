from app.models.domain import AgentLookup, AuthorizationType, User
from tests.factories import add_agent, add_agents_source
from tests.test_api import auth_headers, register

URL = "/api/v1/agents/search"


def seed(factory):
    with factory() as db:
        source = add_agents_source(db)
        add_agent(db, source, "1168287", "ZAVALA TOVAR KARLA PAOLA")
        add_agent(db, source, "885312", "YAÑEZ GOMEZ VANESSA")
        add_agent(db, source, "1151298", "ZAVALA MATEHUALA MARLENE", AuthorizationType.SISTEMAS_TECNOLOGICOS)
        add_agent(db, source, "730249", "ZENIL OJEDA RICARDO")
        add_agent(db, source, "730249", "ZENIL OJEDA RICARDO", AuthorizationType.SISTEMAS_TECNOLOGICOS)
        db.commit()


def test_plate_search_is_public_and_includes_the_official_source(client):
    http, factory = client
    seed(factory)
    body = http.get(URL, params={"q": "1168287"}).json()
    assert body["matched_by"] == "plate"
    assert [r["full_name"] for r in body["results"]] == ["ZAVALA TOVAR KARLA PAOLA"]
    assert body["results"][0]["authorization_type"] == "via_publica"
    assert body["source"] == {
        "title": "Acuerdo 30/2026 (GOCDMX 10-jun-2026)",
        "url": "https://data.consejeria.cdmx.gob.mx/acuerdo-30-2026.pdf",
        "last_reform_date": "2026-06-10",
    }


def test_plate_search_tolerates_spaces_and_dashes(client):
    http, factory = client
    seed(factory)
    assert http.get(URL, params={"q": " 1168 287 "}).json()["results"][0]["plate"] == "1168287"
    assert http.get(URL, params={"q": "1168-287"}).json()["results"][0]["plate"] == "1168287"


def test_plate_in_both_lists_returns_one_result_per_authorization(client):
    http, factory = client
    seed(factory)
    results = http.get(URL, params={"q": "730249"}).json()["results"]
    assert sorted(r["authorization_type"] for r in results) == ["sistemas_tecnologicos", "via_publica"]


def test_name_search_handles_typos_partial_names_and_accents(client):
    http, factory = client
    seed(factory)

    def names(q):
        body = http.get(URL, params={"q": q}).json()
        assert body["matched_by"] == "name"
        return [r["full_name"] for r in body["results"]]

    assert names("zabala tobar karla")[0] == "ZAVALA TOVAR KARLA PAOLA"
    assert names("karla zavala")[0] == "ZAVALA TOVAR KARLA PAOLA"
    assert names("Yáñez Gómez") == ["YAÑEZ GOMEZ VANESSA"]
    assert names("juan perez") == []


def test_unknown_agent_returns_empty_results_with_source(client):
    http, factory = client
    seed(factory)
    body = http.get(URL, params={"q": "999999"}).json()
    assert body["results"] == []
    assert body["source"] is not None


def test_empty_registry_reports_missing_source_instead_of_not_found(client):
    http, _ = client
    body = http.get(URL, params={"q": "1168287"}).json()
    assert body["results"] == []
    assert body["source"] is None


def test_non_current_source_versions_are_not_reported(client):
    http, factory = client
    with factory() as db:
        add_agents_source(db, is_current=False)
        db.commit()
    assert http.get(URL, params={"q": "1168287"}).json()["source"] is None


def test_query_length_is_validated(client):
    http, _ = client
    assert http.get(URL, params={"q": "a"}).status_code == 422
    assert http.get(URL, params={"q": "a" * 101}).status_code == 422
    assert http.get(URL).status_code == 422


def test_lookups_are_recorded_for_anonymous_authenticated_and_invalid_tokens(client):
    http, factory = client
    seed(factory)
    register(http)
    assert http.get(URL, params={"q": "1168287"}).status_code == 200
    assert http.get(URL, params={"q": "1168287"}, headers=auth_headers(http)).status_code == 200
    invalid = http.get(URL, params={"q": "999999"}, headers={"Authorization": "Bearer not-a-real-token"})
    assert invalid.status_code == 200
    with factory() as db:
        user = db.query(User).filter_by(email="ana@example.com").one()
        lookups = db.query(AgentLookup).order_by(AgentLookup.id).all()
        assert [lookup.user_id for lookup in lookups] == [None, user.id, None]
        assert lookups[0].agent_id is not None
        assert lookups[2].agent_id is None


def test_legacy_plate_endpoint_is_gone(client):
    http, factory = client
    seed(factory)
    assert http.get("/api/v1/agents/1168287").status_code == 404

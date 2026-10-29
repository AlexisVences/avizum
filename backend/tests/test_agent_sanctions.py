"""The agent receives verified sanction rows next to the fragments, and an unsupported amount never passes silently.

The seat belt case is the regression test for the failure found in the Phase 4 evaluation: Art. 37 II (5, 7 o 10 UMA
for the belt) and Art. 37 III (motorcycles, other amounts) share inciso letters.
"""
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from langchain_core.messages import AIMessage
from sqlalchemy import select

from app.models.domain import LegalSanction, SanctionStatus
from app.services.agent.agent import build_agent, run_agent
from app.services.agent.amounts import check_amounts
from app.services.agent.context import AgentContext
from app.services.agent.operations import fetch_article, search_legislation
from app.services.ingestion import sanction_store as store
from tests.test_agent import RecordingModel, settings, tool_call
from tests.test_retrieval import FixedQuery, add_chunk, add_source, vec

CHUNKS = json.loads((Path(__file__).parent / "fixtures" / "sanctions" / "chunks.json").read_text(encoding="utf-8"))
SLUG = "reglamento-transito"


def _context(db, user_message="multa por no usar cinturón", **overrides) -> AgentContext:
    cfg = settings()
    return AgentContext(db=db, user_id=None, embeddings=FixedQuery(vec(1, 0)), user_message=user_message, settings=cfg,
                        today=overrides.pop("today", date(2026, 10, 15)), **overrides)


def _seed(db, *keys, verify=True):
    """Chunks from the real fixtures, rows from the extractor, optionally verified like a person would."""
    source = add_source(db, SLUG, "a")
    for key in keys:
        chunk = CHUNKS[key]
        add_chunk(db, source, chunk["article"], chunk["text"], vec(1, 0), fraction=chunk["fraction"], page=46)
    db.flush()
    store.sync_pending(db, SLUG)
    if verify:
        for row in db.scalars(select(LegalSanction)):
            row.status, row.reviewed_by = SanctionStatus.VERIFIED, "Revisora"
            row.reviewed_at = datetime(2026, 10, 16, tzinfo=timezone.utc)
    db.commit()
    return source


def _rows(result):
    return [row for fragment in result["fragmentos"] for row in fragment.get("sanciones", [])]


def test_the_seat_belt_row_carries_its_own_amount_and_the_pesos_are_computed(client):
    _, factory = client
    with factory() as db:
        _seed(db, "37_II", "37_III")
        result = search_legislation(_context(db), "multa cinturón de seguridad conductores")
        assert result["estado"] == "ok"
        belt = next(r for r in _rows(result) if r.get("inciso") == "b" and "cinturón" in r["conducta"])
        assert belt["veces_uma"] == {"minima": "5", "media": "7", "maxima": "10"}
        assert belt["pesos"] == {"minima": "586.55", "media": "821.17", "maxima": "1173.10"}
        assert belt["pronto_pago_50"] == {"minima": "293.28", "media": "410.59", "maxima": "586.55"}
        assert belt["puntos_licencia"] == 1
        # the motorcycle fraction also has an inciso b), with other amounts: it is a different row
        moto_b = [r for r in _rows(result) if r.get("inciso") == "b" and "cinturón" not in r["conducta"]]
        assert moto_b and moto_b[0]["veces_uma"]["minima"] == "10"
        assert result["uma"]["valor_pesos"] == "117.31"
        assert result["nota_sanciones"].startswith("Cada fila")


def test_only_verified_rows_matching_the_current_text_are_served(client):
    _, factory = client
    with factory() as db:
        _seed(db, "37_II", verify=False)
        assert _rows(search_legislation(_context(db), "cinturón")) == []  # pending: invisible

        rows = list(db.scalars(select(LegalSanction).order_by(LegalSanction.ordinal)))
        rows[0].status = SanctionStatus.VERIFIED
        rows[1].status = SanctionStatus.REJECTED
        rows[2].status = SanctionStatus.STALE
        db.commit()
        served = _rows(search_legislation(_context(db), "cinturón"))
        assert [r["inciso"] for r in served] == ["a"]
        assert all("sancion_id" not in r and "id" not in r for r in served)  # row ids were cited as [n] by the model

        rows[0].chunk_hash = "f" * 64  # the text it was verified against is not the text in the database
        db.commit()
        assert _rows(search_legislation(_context(db), "cinturón")) == []


def test_rows_of_a_source_that_is_no_longer_current_are_not_served(client):
    from app.models.domain import LegalChunk
    from app.services.sanctions_lookup import verified_by_chunk

    _, factory = client
    with factory() as db:
        source = _seed(db, "37_II")
        ids = [c.id for c in db.scalars(select(LegalChunk))]
        assert sum(len(v) for v in verified_by_chunk(db, ids).values()) == 5
        source.is_current = False
        db.commit()
        assert verified_by_chunk(db, ids) == {}


def test_a_vehicle_override_is_a_separate_row_and_no_discount_fines_say_so(client):
    _, factory = client
    with factory() as db:
        _seed(db, "conditional")
        result = fetch_article(_context(db), SLUG, "9")
        general, override = _rows(result)
        assert "aplica_a" not in general and override["aplica_a"].startswith("En el caso de vehículos de transporte público")
        assert override["veces_uma"]["minima"] == "20" and override["puntos_licencia"] == 6

    _, factory = client
    with factory() as db:
        row = db.scalars(select(LegalSanction)).first()
        row.article, row.fraction = "33", "II"  # Art. 33 II: the 50% discount does not apply
        db.commit()
        served = _rows(fetch_article(_context(db), SLUG, "9"))
        assert "pronto_pago_50" not in served[0] and "sin_descuento" in served[0]


def test_an_expired_uma_is_flagged_next_to_the_rows(client):
    _, factory = client
    with factory() as db:
        _seed(db, "43")
        result = fetch_article(_context(db, today=date(2028, 1, 1)), SLUG, "43")
        assert "advertencia_uma" in result and len(_rows(result)) == 7


def test_check_amounts_accepts_what_the_tools_returned_and_flags_what_no_tool_said(client):
    _, factory = client
    with factory() as db:
        _seed(db, "37_II")
        ctx = _context(db)
        search_legislation(ctx, "cinturón")
        good = "La multa es de 5, 7 o 10 veces la UMA: $586.55, $821.17 o $1,173.10 [1]."
        assert check_amounts(good, ctx) == []
        paid = "Con pronto pago: $293.28 (mínima). La UMA vale $117.31."
        assert check_amounts(paid, ctx) == []

        invented = "La multa es de 6, 8 o 12 veces la UMA, es decir $999.99 [1]."
        kinds = {(a["clase"], a["valor"]) for a in check_amounts(invented, ctx)}
        assert ("uma_terna", "6, 8 o 12 veces") in kinds
        assert ("pesos", "$999.99") in kinds


def test_the_check_does_not_claim_to_catch_an_amount_that_belongs_to_another_conduct(client):
    """Known limit, on purpose: 10, 15 o 20 is a real amount of Art. 37 II (inciso c), so it is 'supported'. Telling
    that it does not belong to the seat belt is what choosing the right ROW is for, and what the Phase 4 cases measure."""
    _, factory = client
    with factory() as db:
        _seed(db, "37_II", "37_III")
        ctx = _context(db)
        search_legislation(ctx, "cinturón")
        assert check_amounts("La multa es de 10, 15 o 20 veces la UMA [1].", ctx) == []


def test_an_amount_written_in_the_fragment_text_itself_is_supported(client):
    _, factory = client
    with factory() as db:
        source = add_source(db, "codigo-fiscal", "c")
        add_chunk(db, source, "230", "El arrastre de vehículos de hasta 3.5 toneladas cuesta $1,250.50 por servicio.", vec(1, 0))
        db.commit()
        ctx = _context(db)
        search_legislation(ctx, "arrastre grúa")
        assert check_amounts("El arrastre cuesta $1,250.50.", ctx) == []
        assert [a["valor"] for a in check_amounts("El arrastre cuesta $1,500.00.", ctx)] == ["$1,500.00"]


def test_the_served_rows_make_the_right_amount_available_through_the_real_agent(client):
    """End to end with a scripted model: the tool result the model receives contains the seat belt row with its own
    amount, and an answer that invents a figure is flagged at the end of the turn."""
    _, factory = client
    with factory() as db:
        _seed(db, "37_II", "37_III")
        cfg = settings()
        model = RecordingModel(messages=iter([
            tool_call("buscar_legislacion", {"consulta": "multa cinturón de seguridad"}),
            AIMessage(content="La multa es de 7, 9 o 11 veces la UMA, de $1,000.00 [1]."),
        ]), seen=[])
        run = run_agent(build_agent(cfg, model=model), _context(db), "¿cuánto cuesta no usar el cinturón?", history=[], settings=cfg)

        tool_result = next(m.content for m in model.seen[-1] if getattr(m, "type", "") == "tool")
        payload = json.loads(tool_result)
        belt = [r for f in payload["fragmentos"] for r in f.get("sanciones", []) if r.get("inciso") == "b" and "cinturón" in r["conducta"]]
        assert belt and belt[0]["veces_uma"]["minima"] == "5"
        assert {a["clase"] for a in run.anomalies if a["tipo"] == "monto_no_respaldado"} == {"uma_terna", "pesos"}


def test_thousands_with_a_comma_are_one_number_not_a_phantom_amount(client):
    """"de 500 a 1,000 veces la UMA" was read as "000 veces la UMA" and flagged as unsupported."""
    _, factory = client
    with factory() as db:
        source = add_source(db, "ley-movilidad", "m")
        add_chunk(db, source, "251", "Se sancionará con multa de 500 a 1,000 veces la Unidad de Medida y Actualización.", vec(1, 0))
        db.commit()
        ctx = _context(db)
        search_legislation(ctx, "multa transporte peligrosos")
        assert check_amounts("La multa va de 500 a 1,000 veces la UMA.", ctx) == []
        assert [a["valor"] for a in check_amounts("La multa es de 2,000 veces la UMA.", ctx)] == ["2,000 veces la UMA"]


def test_multiples_the_law_writes_in_words_count_as_supported(client):
    """Ley de Movilidad writes "de quinientos a seiscientos ochenta veces la Unidad de Medida"; the answer says 500 a 680."""
    _, factory = client
    with factory() as db:
        source = add_source(db, "ley-movilidad", "m")
        add_chunk(db, source, "251", "Se sancionará con multa de quinientos a seiscientos ochenta veces la Unidad de Medida y Actualización de la Ciudad de México vigente.", vec(1, 0))
        db.commit()
        ctx = _context(db)
        search_legislation(ctx, "multa concesión")
        assert check_amounts("La multa va de 500 a 680 veces la UMA.", ctx) == []
        assert [a["valor"] for a in check_amounts("La multa va de 500 a 700 veces la UMA.", ctx)] == ["700 veces la UMA"]


def test_unverified_rows_flag_the_fragment_and_its_prose_amounts_stop_counting_as_support(client):
    _, factory = client
    with factory() as db:
        _seed(db, "37_II", verify=False)  # extracted but nobody reviewed it
        ctx = _context(db)
        result = search_legislation(ctx, "cinturón")
        assert _rows(result) == []
        flagged = [f for f in result["fragmentos"] if "sanciones_sin_verificar" in f]
        assert flagged and "NO están verificadas" in flagged[0]["sanciones_sin_verificar"]
        # the article text says "5, 7 o 10 veces la UMA", yet repeating it is now an unsupported amount
        assert check_amounts("Son 5, 7 o 10 veces la UMA [1].", ctx)[0]["tipo"] == "monto_no_respaldado"


def test_stale_rows_are_flagged_as_unverified_too(client):
    _, factory = client
    with factory() as db:
        _seed(db, "37_II")
        rows = list(db.scalars(select(LegalSanction)))
        for row in rows:
            row.chunk_hash = "f" * 64  # the text changed after the review
        db.commit()
        result = search_legislation(_context(db), "cinturón")
        assert _rows(result) == []
        assert any("sanciones_sin_verificar" in f for f in result["fragmentos"])


def test_fully_verified_fragments_are_not_flagged_and_their_amounts_remain_supported(client):
    _, factory = client
    with factory() as db:
        _seed(db, "37_II")
        ctx = _context(db)
        result = search_legislation(ctx, "cinturón")
        assert not any("sanciones_sin_verificar" in f for f in result["fragmentos"])
        assert check_amounts("Son 5, 7 o 10 veces la UMA [1].", ctx) == []

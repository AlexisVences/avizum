from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from app.core.config import Settings
from app.models.domain import (
    AgentLookup, Conversation, Message, MessageFeedback, MessageRole, MessageStatus, UserRole,
)
from app.services.admin.overview import build_overview
from tests.admin_support import make_user

URL = "/api/v1/admin/overview"
CDMX = ZoneInfo("America/Mexico_City")
NOW = datetime(2026, 10, 20, 15, 0, tzinfo=CDMX)


def _admin(factory):
    return make_user(factory, email="admin@example.com", role=UserRole.ADMIN)[1]


def _chat(factory, user_id, rows):
    """rows: (role, created_at, status, input_tokens, output_tokens); returns message ids."""
    with factory() as db:
        conv = Conversation(user_id=user_id, title="t")
        db.add(conv)
        db.flush()
        messages = [
            Message(
                conversation_id=conv.id, role=role, content="x", created_at=when,
                status=status, input_tokens=tin, output_tokens=tout,
            )
            for role, when, status, tin, tout in rows
        ]
        db.add_all(messages)
        db.commit()
        return [m.id for m in messages]


def _ask(when, status=MessageStatus.COMPLETE):
    return (MessageRole.USER, when, status, None, None)


def _answer(when, status=MessageStatus.COMPLETE, tin=None, tout=None):
    return (MessageRole.ASSISTANT, when, status, tin, tout)


def _overview(factory, days=30, now=NOW):
    with factory() as db:
        return build_overview(db, days=days, now=now)


def test_cuenta_solo_preguntas_de_personas_dentro_del_periodo(client):
    _, factory = client
    uid = make_user(factory, email="a@example.com")[0].id
    _chat(factory, uid, [
        _ask(NOW - timedelta(days=1)),
        _ask(NOW - timedelta(days=10)),  # fuera de 7 días
        _answer(NOW - timedelta(days=1)),  # no es una pregunta
    ])
    assert _overview(factory, days=7).questions == 1
    assert _overview(factory, days=30).questions == 2


def test_active_users_cuenta_personas_distintas(client):
    _, factory = client
    a = make_user(factory, email="a@example.com")[0].id
    b = make_user(factory, email="b@example.com")[0].id
    _chat(factory, a, [_ask(NOW - timedelta(days=1)), _ask(NOW - timedelta(days=2))])
    _chat(factory, b, [_ask(NOW - timedelta(days=1))])
    result = _overview(factory)
    assert result.questions == 3
    assert result.active_users == 2


def test_la_serie_incluye_todos_los_dias_con_0_donde_no_hubo_preguntas(client):
    _, factory = client
    uid = make_user(factory, email="a@example.com")[0].id
    _chat(factory, uid, [_ask(NOW - timedelta(days=2)), _ask(NOW - timedelta(days=2))])
    series = _overview(factory, days=7).series
    assert [p.date.isoformat() for p in series] == [
        "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-17",
        "2026-10-18", "2026-10-19", "2026-10-20",
    ]
    assert [p.questions for p in series] == [0, 0, 0, 0, 2, 0, 0]
    assert len(_overview(factory, days=90).series) == 90


def test_un_mensaje_a_las_2330_de_la_cdmx_cae_en_su_dia_y_no_en_el_siguiente_utc(client):
    _, factory = client
    uid = make_user(factory, email="a@example.com")[0].id
    late = datetime(2026, 10, 19, 23, 30, tzinfo=CDMX)  # 05:30 UTC del día 20
    _chat(factory, uid, [_ask(late)])
    by_day = {p.date.isoformat(): p.questions for p in _overview(factory, days=7).series}
    assert by_day["2026-10-19"] == 1
    assert by_day["2026-10-20"] == 0


def test_feedback_rate_es_none_sin_calificaciones_y_089_con_40_positivas_y_5_negativas(client):
    _, factory = client
    assert _overview(factory).feedback_rate is None
    assert _overview(factory).feedback_rated == 0
    with factory() as db:
        for i in range(45):
            user = make_user(factory, email=f"u{i}@example.com")[0]
            conv = Conversation(user_id=user.id, title="t")
            db.add(conv)
            db.flush()
            msg = Message(conversation_id=conv.id, role=MessageRole.ASSISTANT, content="x")
            db.add(msg)
            db.flush()
            db.add(MessageFeedback(
                message_id=msg.id, user_id=user.id, value=1 if i < 40 else -1,
                created_at=NOW - timedelta(days=1),
            ))
        db.commit()
    result = _overview(factory)
    assert (result.feedback_up, result.feedback_down, result.feedback_rated) == (40, 5, 45)
    assert result.feedback_rate == pytest.approx(0.89, abs=0.005)


def test_error_rate_cuenta_respuestas_con_status_error_entre_las_respuestas(client):
    _, factory = client
    uid = make_user(factory, email="a@example.com")[0].id
    assert _overview(factory).error_rate is None
    day = NOW - timedelta(days=1)
    _chat(factory, uid, [
        _ask(day), _answer(day), _answer(day), _answer(day),
        _answer(day, MessageStatus.ERROR),
    ])
    result = _overview(factory)
    assert result.answers_with_error == 1
    assert result.error_rate == pytest.approx(0.25)


def test_el_costo_usa_los_precios_de_settings(client):
    _, factory = client
    uid = make_user(factory, email="a@example.com")[0].id
    _chat(factory, uid, [
        _answer(NOW - timedelta(days=1), tin=600_000, tout=400_000),
        _answer(NOW - timedelta(days=1), tin=400_000, tout=600_000),
        _answer(NOW - timedelta(days=1)),  # tokens NULL cuentan como 0
    ])
    result = _overview(factory)
    assert (result.tokens_input, result.tokens_output) == (1_000_000, 1_000_000)
    assert result.cost_usd == Decimal("2.25")


def test_el_resumen_cuenta_altas_y_consultas_de_agentes_y_serializa_el_costo_como_texto(client):
    http, factory = client
    headers = _admin(factory)
    with factory() as db:
        db.add(AgentLookup(created_at=datetime.now(timezone.utc)))
        db.commit()
    body = http.get(URL, headers=headers).json()
    assert body["days"] == 30
    assert body["new_users"] == 1
    assert body["agent_lookups"] == 1
    assert body["cost_usd"] == "0.00"
    assert body["attention"] == []
    assert len(body["series"]) == 30


def test_days_15_responde_422(client):
    http, factory = client
    assert http.get(f"{URL}?days=15", headers=_admin(factory)).status_code == 422


def test_403_a_un_usuario_normal_y_401_sin_sesion(client):
    http, factory = client
    _, headers = make_user(factory, email="u@example.com")
    assert http.get(URL, headers=headers).status_code == 403
    assert http.get(URL).status_code == 401


def test_los_precios_tienen_un_valor_por_defecto_positivo():
    settings = Settings()
    assert settings.llm_price_input_per_million > 0
    assert settings.llm_price_output_per_million > 0

from datetime import datetime, timedelta, timezone

from app.models.domain import Conversation, Message, MessageRole, User, UserRole
from tests.admin_support import make_user

URL = "/api/v1/admin/users"


def _admin(factory):
    return make_user(factory, email="admin@example.com", role=UserRole.ADMIN)[1]


def _person(factory, email, first="Ana", last="Ruiz", **kwargs) -> int:
    user, _ = make_user(factory, email=email, **kwargs)
    with factory() as db:
        row = db.get(User, user.id)
        row.first_name, row.last_name = first, last
        db.commit()
    return user.id


def _messages(factory, user_id, users=0, assistant=0, when=None):
    when = when or datetime.now(timezone.utc)
    with factory() as db:
        conv = Conversation(user_id=user_id, title="t")
        db.add(conv)
        db.flush()
        for i in range(users):
            db.add(Message(conversation_id=conv.id, role=MessageRole.USER, content="q", created_at=when))
        for i in range(assistant):
            db.add(Message(conversation_id=conv.id, role=MessageRole.ASSISTANT, content="a", created_at=when))
        db.commit()


def test_un_usuario_normal_recibe_403(client):
    http, factory = client
    _, headers = make_user(factory, email="u@example.com")
    assert http.get(URL, headers=headers).status_code == 403
    assert http.get(URL).status_code == 401


def test_q_encuentra_por_correo_y_por_nombre_sin_acentos(client):
    http, factory = client
    headers = _admin(factory)
    _person(factory, "maria@example.com", first="María", last="López")
    _person(factory, "otro@dominio.mx", first="Pedro", last="Gómez")
    by_name = http.get(URL, params={"q": "lopez"}, headers=headers).json()
    assert [r["email"] for r in by_name["items"]] == ["maria@example.com"]
    by_upper = http.get(URL, params={"q": "GOMEZ"}, headers=headers).json()
    assert [r["email"] for r in by_upper["items"]] == ["otro@dominio.mx"]
    by_email = http.get(URL, params={"q": "dominio"}, headers=headers).json()
    assert by_email["total"] == 1


def test_filtra_por_rol_estado_y_verificado(client):
    http, factory = client
    headers = _admin(factory)
    _person(factory, "off@example.com", is_active=False)
    _person(factory, "unv@example.com", verified=False)
    _person(factory, "ok@example.com")

    def emails(**params):
        data = http.get(URL, params=params, headers=headers).json()
        return sorted(r["email"] for r in data["items"])

    assert emails(role="admin") == ["admin@example.com"]
    assert emails(active="false") == ["off@example.com"]
    assert emails(verified="false") == ["unv@example.com"]
    assert emails(role="user", active="true", verified="true") == ["ok@example.com"]


def test_pagina_45_personas_page_size_20_page_3(client):
    http, factory = client
    headers = _admin(factory)
    for i in range(44):
        _person(factory, f"p{i}@example.com")
    data = http.get(URL, params={"page": 3, "page_size": 20}, headers=headers).json()
    assert len(data["items"]) == 5
    assert data["total"] == 45
    assert data["page"] == 3 and data["page_size"] == 20


def test_page_fuera_de_rango_devuelve_items_vacios_y_total_correcto(client):
    http, factory = client
    headers = _admin(factory)
    _person(factory, "a@example.com")
    response = http.get(URL, params={"page": 99}, headers=headers)
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 2


def test_page_size_1000_responde_422(client):
    http, factory = client
    headers = _admin(factory)
    assert http.get(URL, params={"page_size": 1000}, headers=headers).status_code == 422


def test_persona_sin_mensajes_tiene_actividad_nula_y_aparece_al_ordenar(client):
    http, factory = client
    headers = _admin(factory)
    quiet = _person(factory, "quiet@example.com")
    busy = _person(factory, "busy@example.com")
    _messages(factory, busy, users=2, assistant=2)
    for sort in ("activity", "questions"):
        for direction in ("true", "false"):
            data = http.get(URL, params={"sort": sort, "descending": direction}, headers=headers).json()
            assert data["total"] == 3
            row = next(r for r in data["items"] if r["id"] == quiet)
            assert row["last_activity_at"] is None
            assert row["questions_count"] == 0
    for direction in ("true", "false"):
        items = http.get(URL, params={"sort": "activity", "descending": direction}, headers=headers).json()["items"]
        assert items[0]["id"] == busy
        assert items[-1]["last_activity_at"] is None


def test_ordena_por_preguntas_descendente(client):
    http, factory = client
    headers = _admin(factory)
    a = _person(factory, "a@example.com")
    b = _person(factory, "b@example.com")
    _messages(factory, a, users=1, assistant=5)
    _messages(factory, b, users=3)
    items = http.get(URL, params={"sort": "questions", "descending": "true"}, headers=headers).json()["items"]
    assert [r["id"] for r in items][:2] == [b, a]
    assert items[0]["questions_count"] == 3
    assert items[1]["questions_count"] == 1

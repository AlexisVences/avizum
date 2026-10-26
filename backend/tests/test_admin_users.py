from datetime import datetime, timezone

import pytest

from app.models.domain import AdminAuditLog, Conversation, Message, MessageRole, User, UserRole
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
        for _ in range(users):
            db.add(Message(conversation_id=conv.id, role=MessageRole.USER, content="q",
                           created_at=when))
        for _ in range(assistant):
            db.add(Message(conversation_id=conv.id, role=MessageRole.ASSISTANT, content="a",
                           created_at=when))
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
            params = {"sort": sort, "descending": direction}
            data = http.get(URL, params=params, headers=headers).json()
            assert data["total"] == 3
            row = next(r for r in data["items"] if r["id"] == quiet)
            assert row["last_activity_at"] is None
            assert row["questions_count"] == 0
    for direction in ("true", "false"):
        params = {"sort": "activity", "descending": direction}
        items = http.get(URL, params=params, headers=headers).json()["items"]
        assert items[0]["id"] == busy
        assert items[-1]["last_activity_at"] is None


def test_ordena_por_preguntas_descendente(client):
    http, factory = client
    headers = _admin(factory)
    a = _person(factory, "a@example.com")
    b = _person(factory, "b@example.com")
    _messages(factory, a, users=1, assistant=5)
    _messages(factory, b, users=3)
    params = {"sort": "questions", "descending": "true"}
    items = http.get(URL, params=params, headers=headers).json()["items"]
    assert [r["id"] for r in items][:2] == [b, a]
    assert items[0]["questions_count"] == 3
    assert items[1]["questions_count"] == 1


def test_q_trata_porcentaje_y_guion_bajo_como_texto_literal(client):
    http, factory = client
    headers = _admin(factory)
    _person(factory, "plain@example.com")
    _person(factory, "pct@example.com", first="100%")
    _person(factory, "und@example.com", last="a_b")
    items = http.get(URL, params={"q": "%"}, headers=headers).json()["items"]
    assert [r["email"] for r in items] == ["pct@example.com"]
    assert http.get(URL, params={"q": "_"}, headers=headers).json()["total"] == 1
    assert http.get(URL, params={"q": "zzz%"}, headers=headers).json()["total"] == 0


def test_page_por_encima_del_tope_responde_422(client):
    http, factory = client
    headers = _admin(factory)
    assert http.get(URL, params={"page": 1_000_001}, headers=headers).status_code == 422


def test_q_con_nombre_completo_exige_todas_las_palabras(client):
    http, factory = client
    headers = _admin(factory)
    _person(factory, "maria@example.com", first="María", last="López")
    _person(factory, "mario@example.com", first="Mario", last="López")
    data = http.get(URL, params={"q": "maria lopez"}, headers=headers).json()
    assert [r["email"] for r in data["items"]] == ["maria@example.com"]
    assert http.get(URL, params={"q": "  maria  zzz "}, headers=headers).json()["total"] == 0


# --- Task 1.3: role and active changes ---

def _me(factory, email="admin@example.com"):
    user, headers = make_user(factory, email=email, role=UserRole.ADMIN)
    return user.id, headers


def test_un_administrador_no_puede_cambiar_su_propio_rol_ni_desactivarse(client):
    http, factory = client
    me, headers = _me(factory)
    _me(factory, "otro@example.com")
    for body in ({"role": "user"}, {"is_active": False}):
        res = http.patch(f"{URL}/{me}", json=body, headers=headers)
        assert res.status_code == 409
        assert res.json()["detail"]["code"] == "cannot_modify_self"
        assert res.json()["detail"]["message"]


def test_no_se_puede_quitar_el_rol_ni_desactivar_al_ultimo_administrador_activo(client):
    http, factory = client
    actor_id, _ = _me(factory)
    target = _person(factory, "t@example.com", role=UserRole.ADMIN)
    # Over HTTP the actor is always a second active admin, so the guard is only reachable by
    # calling the service with an actor who no longer counts as an active admin.
    from app.services.admin.users import AdminRuleError, update_user

    with factory() as db:
        db.get(User, actor_id).is_active = False
        db.commit()
    with factory() as db:
        actor = db.get(User, actor_id)
        for kwargs in ({"role": UserRole.USER}, {"is_active": False}):
            with pytest.raises(AdminRuleError) as raised:
                update_user(db, actor=actor, target_id=target, role=kwargs.get("role"),
                            is_active=kwargs.get("is_active"))
            assert raised.value.code == "last_admin"
            db.rollback()


def test_con_dos_administradores_si_se_puede_degradar_a_otro(client):
    http, factory = client
    _, headers = _me(factory)
    other = _person(factory, "t@example.com", role=UserRole.ADMIN)
    res = http.patch(f"{URL}/{other}", json={"role": "user"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["role"] == "user"


def test_desactivar_invalida_su_sesion(client):
    http, factory = client
    _, headers = _me(factory)
    target, target_headers = make_user(factory, email="t@example.com")
    assert http.get("/api/v1/users/me", headers=target_headers).status_code == 200
    res = http.patch(f"{URL}/{target.id}", json={"is_active": False}, headers=headers)
    assert res.status_code == 200
    assert http.get("/api/v1/users/me", headers=target_headers).status_code == 401
    with factory() as db:
        assert db.get(User, target.id).token_version == target.token_version + 1


def test_reactivar_permite_iniciar_sesion(client):
    http, factory = client
    _, headers = _me(factory)
    http.post("/api/v1/auth/register", json={
        "first_name": "Ana", "last_name": "L", "email": "ana@example.com",
        "password": "a secure password"})
    with factory() as db:
        target = db.query(User).filter_by(email="ana@example.com").one().id
    login = {"email": "ana@example.com", "password": "a secure password"}
    http.patch(f"{URL}/{target}", json={"is_active": False}, headers=headers)
    assert http.post("/api/v1/auth/login", json=login).status_code == 401
    assert http.patch(f"{URL}/{target}", json={"is_active": True},
                      headers=headers).status_code == 200
    assert http.post("/api/v1/auth/login", json=login).status_code == 200


def test_cada_cambio_queda_en_admin_audit_log_con_actor_y_objetivo(client):
    http, factory = client
    me, headers = _me(factory)
    target = _person(factory, "t@example.com")
    http.patch(f"{URL}/{target}", json={"role": "admin"}, headers=headers)
    http.patch(f"{URL}/{target}", json={"is_active": False}, headers=headers)
    http.patch(f"{URL}/{target}", json={"is_active": True}, headers=headers)
    with factory() as db:
        rows = db.query(AdminAuditLog).order_by(AdminAuditLog.id).all()
        assert [r.action for r in rows] == [
            "user.role_changed", "user.deactivated", "user.reactivated"]
        assert all(r.actor_id == me and r.target_user_id == target for r in rows)
        assert rows[0].detail == {"from": "user", "to": "admin"}


def test_repetir_el_mismo_valor_no_crea_registro(client):
    http, factory = client
    _, headers = _me(factory)
    target = _person(factory, "t@example.com")
    res = http.patch(f"{URL}/{target}", json={"role": "user", "is_active": True}, headers=headers)
    assert res.status_code == 200
    with factory() as db:
        assert db.query(AdminAuditLog).count() == 0
        assert db.get(User, target).token_version == 0


def test_un_usuario_inexistente_da_404(client):
    http, factory = client
    _, headers = _me(factory)
    assert http.patch(f"{URL}/99999", json={"role": "user"}, headers=headers).status_code == 404


def test_cambiar_rol_exige_administrador(client):
    http, factory = client
    _, headers = make_user(factory, email="u@example.com")
    assert http.patch(f"{URL}/1", json={"role": "admin"}, headers=headers).status_code == 403
    assert http.patch(f"{URL}/1", json={"role": "admin"}).status_code == 401

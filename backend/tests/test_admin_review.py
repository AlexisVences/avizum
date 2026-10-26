import pytest
from sqlalchemy.exc import IntegrityError

from app.models.domain import (
    AdminAuditLog, Conversation, Message, MessageFeedback, MessageReview, MessageRole,
    MessageStatus, User, UserRole,
)
from tests.admin_support import make_user


def _assistant_message(factory, user_id: int) -> int:
    with factory() as db:
        conv = Conversation(user_id=user_id, title="t")
        db.add(conv)
        db.flush()
        msg = Message(conversation_id=conv.id, role=MessageRole.ASSISTANT, content="respuesta")
        db.add(msg)
        db.commit()
        return msg.id


def test_una_revision_por_mensaje_y_se_borra_con_el_mensaje(client):
    _, factory = client
    admin, _ = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    message_id = _assistant_message(factory, admin.id)
    with factory() as db:
        db.add(MessageReview(message_id=message_id, reviewer_id=admin.id, note="ok"))
        db.commit()
        db.add(MessageReview(message_id=message_id, reviewer_id=admin.id))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        db.delete(db.get(Message, message_id))
        db.commit()
        assert db.query(MessageReview).count() == 0


URL = "/api/v1/admin/review-queue"
CITATION = {
    "source_slug": "reglamento", "source_title": "Reglamento", "article": "10",
    "fraction": None, "page": 3, "url": "https://example.com/r.pdf",
}
SEARCH = [{"name": "buscar_legislacion", "args": {"consulta": "x"}, "estado": "ok"}]


def _admin(factory):
    return make_user(factory, email="admin@example.com", role=UserRole.ADMIN)[1]


def _turn(factory, user_id, *, question="¿qué pasa?", status=MessageStatus.COMPLETE,
          citations=None, tool_calls=None, thumbs=None, conversation_id=None):
    """Create a question and its answer; returns (answer id, conversation id)."""
    with factory() as db:
        if conversation_id is None:
            conv = Conversation(user_id=user_id, title="t")
            db.add(conv)
            db.flush()
            conversation_id = conv.id
        db.add(Message(conversation_id=conversation_id, role=MessageRole.USER, content=question))
        db.flush()
        answer = Message(
            conversation_id=conversation_id, role=MessageRole.ASSISTANT, content="respuesta",
            status=status, citations=citations, tool_calls=tool_calls,
        )
        db.add(answer)
        db.flush()
        if thumbs is not None:
            db.add(MessageFeedback(message_id=answer.id, user_id=user_id, value=thumbs))
        db.commit()
        return answer.id, conversation_id


def _queue(http, headers, **params):
    response = http.get(URL, headers=headers, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_una_respuesta_con_pulgar_abajo_entra_con_razon_negative(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    mid, _ = _turn(factory, person.id, citations=[CITATION], tool_calls=SEARCH, thumbs=-1)
    body = _queue(http, headers)
    assert body["total"] == 1
    item = body["items"][0]
    assert item["message_id"] == mid
    assert item["reasons"] == ["negative"]
    assert item["tools"] == ["buscar_legislacion"]
    assert item["citations"] == [CITATION]
    assert item["answer"] == "respuesta"
    assert item["reviewed"] is False and item["note"] is None


def test_una_con_error_entra(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    _turn(factory, person.id, status=MessageStatus.ERROR)
    item = _queue(http, headers)["items"][0]
    assert item["reasons"] == ["error"]


def test_una_completa_sin_citas_pero_con_busquedas_entra_como_uncited(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    _turn(factory, person.id, citations=None, tool_calls=SEARCH)
    _turn(factory, person.id, citations=[], tool_calls=SEARCH + SEARCH)
    body = _queue(http, headers)
    assert body["total"] == 2
    assert all(i["reasons"] == ["uncited"] for i in body["items"])
    assert body["items"][0]["tools"] == ["buscar_legislacion"]


def test_una_negativa_por_alcance_sin_herramientas_no_entra(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    _turn(factory, person.id, citations=None, tool_calls=None)
    _turn(factory, person.id, citations=[], tool_calls=[])
    assert _queue(http, headers)["total"] == 0


def test_una_bien_calificada_y_citada_no_entra(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    _turn(factory, person.id, citations=[CITATION], tool_calls=SEARCH, thumbs=1)
    assert _queue(http, headers)["total"] == 0


def test_varias_razones_en_un_solo_elemento(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    _turn(factory, person.id, tool_calls=SEARCH, thumbs=-1)
    item = _queue(http, headers)["items"][0]
    assert sorted(item["reasons"]) == ["negative", "uncited"]


def test_la_pregunta_mostrada_es_la_anterior_de_esa_conversacion(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    with factory() as db:
        conv_a = Conversation(user_id=person.id, title="a")
        conv_b = Conversation(user_id=person.id, title="b")
        conv_c = Conversation(user_id=person.id, title="c")
        db.add_all([conv_a, conv_b, conv_c])
        db.flush()

        def add(conv, role, content, status=MessageStatus.COMPLETE):
            db.add(Message(conversation_id=conv.id, role=role, content=content, status=status))
            db.flush()

        add(conv_a, MessageRole.USER, "primera")
        add(conv_a, MessageRole.ASSISTANT, "ok a1")
        add(conv_a, MessageRole.USER, "segunda")
        add(conv_b, MessageRole.USER, "de la otra conversación")
        add(conv_a, MessageRole.ASSISTANT, "falla a2", MessageStatus.ERROR)
        add(conv_b, MessageRole.ASSISTANT, "falla b1", MessageStatus.ERROR)
        add(conv_c, MessageRole.ASSISTANT, "sola", MessageStatus.ERROR)
        db.commit()
    asked = {i["answer"]: i["question"] for i in _queue(http, headers)["items"]}
    assert asked == {
        "falla a2": "segunda", "falla b1": "de la otra conversación", "sola": "",
    }


def _keys(value):
    if isinstance(value, dict):
        for key, inner in value.items():
            yield key
            yield from _keys(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from _keys(inner)


def test_el_cuerpo_de_la_respuesta_no_contiene_nombre_correo_ni_user_id(client):
    http, factory = client
    headers = _admin(factory)
    with factory() as db:
        person = User(
            first_name="Zacarías", last_name="Quintanilla", email="zacarias.q@example.com",
            password_hash=None, role=UserRole.USER,
        )
        db.add(person)
        db.commit()
        person_id = person.id
    _turn(factory, person_id, status=MessageStatus.ERROR, tool_calls=SEARCH, thumbs=-1)
    response = http.get(URL, headers=headers)
    body = response.json()
    assert body["total"] == 1
    forbidden = {
        "user_id", "conversation_id", "user", "email", "first_name", "last_name", "name",
        "actor_id", "reviewer_id", "id",
    }
    assert not forbidden & set(_keys(body))
    text = response.text
    for secret in ("Zacarías", "Zacar\\u00edas", "Quintanilla", "zacarias.q@example.com"):
        assert secret not in text


def test_filtra_por_reviewed_y_por_reason(client):
    http, factory = client
    headers = _admin(factory)
    admin_id = make_user(factory, email="r@example.com", role=UserRole.ADMIN)[0].id
    person, _ = make_user(factory, email="p@example.com")
    neg, _ = _turn(factory, person.id, tool_calls=SEARCH, citations=[CITATION], thumbs=-1)
    err, _ = _turn(factory, person.id, status=MessageStatus.ERROR)
    with factory() as db:
        db.add(MessageReview(message_id=err, reviewer_id=admin_id, note="visto"))
        db.commit()
    assert [i["message_id"] for i in _queue(http, headers, reviewed="false")["items"]] == [neg]
    done = _queue(http, headers, reviewed="true")["items"]
    assert [i["message_id"] for i in done] == [err]
    assert done[0]["reviewed"] is True and done[0]["note"] == "visto"
    assert [i["message_id"] for i in _queue(http, headers, reason="error")["items"]] == [err]
    assert [i["message_id"] for i in _queue(http, headers, reason="negative")["items"]] == [neg]
    assert _queue(http, headers, reason="uncited")["total"] == 0
    assert [i["message_id"] for i in _queue(http, headers)["items"]] == [err, neg]


def test_paginacion_y_limites(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    for _i in range(3):
        _turn(factory, person.id, status=MessageStatus.ERROR)
    body = _queue(http, headers, page=2, page_size=2)
    assert body["total"] == 3 and len(body["items"]) == 1 and body["page_size"] == 2
    assert _queue(http, headers, page=99)["items"] == []
    assert http.get(URL, headers=headers, params={"page_size": 51}).status_code == 422
    assert http.get(URL, headers=headers, params={"page": 0}).status_code == 422


def test_al_eliminar_a_la_persona_sus_filas_desaparecen_de_la_cola(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    mid, _ = _turn(factory, person.id, status=MessageStatus.ERROR)
    with factory() as db:
        db.add(MessageReview(message_id=mid))
        db.commit()
    assert _queue(http, headers)["total"] == 1
    response = http.request(
        "DELETE", f"/api/v1/admin/users/{person.id}", json={"confirm_email": "p@example.com"},
        headers=headers,
    )
    assert response.status_code == 204
    assert _queue(http, headers)["total"] == 0
    with factory() as db:
        assert db.query(MessageReview).count() == 0


def test_la_cola_exige_administrador(client):
    http, factory = client
    _, user_headers = make_user(factory, email="u@example.com")
    assert http.get(URL).status_code == 401
    assert http.get(URL, headers=user_headers).status_code == 403


def _post(http, headers, message_id, **body):
    return http.post(f"{URL}/{message_id}/review", headers=headers, json=body)


def _queued(factory, **kwargs):
    person, _ = make_user(factory, email=f"p{kwargs.pop('n', 0)}@example.com")
    return _turn(factory, person.id, **kwargs)[0]


def test_marcar_dos_veces_no_duplica_ni_falla(client):
    http, factory = client
    headers = _admin(factory)
    mid = _queued(factory, status=MessageStatus.ERROR)
    assert _post(http, headers, mid, note="primera").status_code == 200
    second = _post(http, headers, mid, note="segunda")
    assert second.status_code == 200
    assert second.json() == {"message_id": mid, "reviewed": True, "note": "segunda"}
    with factory() as db:
        assert db.query(MessageReview).count() == 1
        assert db.query(MessageReview).one().note == "segunda"
        assert db.query(AdminAuditLog).filter_by(action="review.marked").count() == 1


def test_la_revision_guarda_la_nota_y_quien(client):
    http, factory = client
    admin, headers = make_user(factory, email="admin@example.com", role=UserRole.ADMIN)
    mid = _queued(factory, status=MessageStatus.ERROR)
    assert _post(http, headers, mid, note="falta el artículo").status_code == 200
    with factory() as db:
        review = db.query(MessageReview).one()
        assert (review.message_id, review.reviewer_id, review.note) == (
            mid, admin.id, "falta el artículo",
        )
    item = _queue(http, headers, reviewed="true")["items"][0]
    assert item["reviewed"] is True and item["note"] == "falta el artículo"
    assert _post(http, headers, mid).json()["note"] is None


def test_queda_en_la_auditoria(client):
    http, factory = client
    admin, headers = make_user(factory, email="admin@example.com", role=UserRole.ADMIN)
    mid = _queued(factory, status=MessageStatus.ERROR)
    _post(http, headers, mid, note="texto de la nota")
    with factory() as db:
        row = db.query(AdminAuditLog).one()
        assert row.action == "review.marked"
        assert row.actor_id == admin.id
        assert row.detail == {"message_id": mid}


def test_la_nota_de_mas_de_500_caracteres_da_422(client):
    http, factory = client
    headers = _admin(factory)
    mid = _queued(factory, status=MessageStatus.ERROR)
    assert _post(http, headers, mid, note="x" * 501).status_code == 422
    assert _post(http, headers, mid, note="x" * 500).status_code == 200


def test_eval_case_devuelve_verified_false_y_expected_desde_las_citas(client):
    http, factory = client
    headers = _admin(factory)
    other = {**CITATION, "source_slug": "ley", "article": "5"}
    no_slug = {**CITATION, "source_slug": None, "article": "9"}
    mid = _queued(
        factory, question="¿cuánto es la multa?", status=MessageStatus.ERROR,
        citations=[CITATION, other, CITATION, no_slug], tool_calls=SEARCH, thumbs=-1,
    )
    response = http.get(f"{URL}/{mid}/eval-case", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": f"p{mid}",
        "question": "¿cuánto es la multa?",
        "coverage": "full",
        "expected": [
            {"source": "reglamento", "article": "10"}, {"source": "ley", "article": "5"},
        ],
        "notes": "Exportado de producción; etiquetas por verificar",
        "verified": False,
    }
    assert "p@example" not in response.text


def test_un_mensaje_que_no_esta_en_la_cola_da_404(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    fine, conv = _turn(factory, person.id, citations=[CITATION], tool_calls=SEARCH, thumbs=1)
    with factory() as db:
        user_msg = db.query(Message).filter_by(role=MessageRole.USER).one().id
    for missing in (fine, user_msg, 99999):
        assert _post(http, headers, missing).status_code == 404
        assert http.get(f"{URL}/{missing}/eval-case", headers=headers).status_code == 404
    with factory() as db:
        assert db.query(MessageReview).count() == 0


def test_los_endpoints_de_revision_exigen_administrador(client):
    http, factory = client
    _, user_headers = make_user(factory, email="u@example.com")
    mid = _queued(factory, status=MessageStatus.ERROR)
    for call in (
        lambda h: http.post(f"{URL}/{mid}/review", headers=h, json={}),
        lambda h: http.get(f"{URL}/{mid}/eval-case", headers=h),
    ):
        assert call({}).status_code == 401
        assert call(user_headers).status_code == 403


def test_una_clave_extra_en_una_cita_guardada_no_llega_a_la_respuesta(client):
    http, factory = client
    headers = _admin(factory)
    _queued(factory, status=MessageStatus.ERROR, citations=[{**CITATION, "internal_note": "x"}])
    item = _queue(http, headers)["items"][0]
    assert item["citations"] == [CITATION]
    assert "internal_note" not in str(item)


def test_la_seleccion_sql_y_las_razones_coinciden(client):
    http, factory = client
    headers = _admin(factory)
    person, _ = make_user(factory, email="p@example.com")
    bad_tools = [{"args": {}}, "texto", {"name": 3}]
    _turn(factory, person.id, citations=[CITATION], tool_calls=SEARCH, thumbs=-1)
    _turn(factory, person.id, status=MessageStatus.ERROR)
    _turn(factory, person.id, citations=[], tool_calls=SEARCH)
    _turn(factory, person.id, citations=None, tool_calls=None)  # rechazo sin herramientas
    _turn(factory, person.id, citations=[], tool_calls=bad_tools)
    _turn(factory, person.id, citations={"a": 1}, tool_calls=SEARCH)
    body = _queue(http, headers)
    assert body["total"] == 5
    assert all(item["reasons"] for item in body["items"])
    by_reason = sorted(tuple(item["reasons"]) for item in body["items"])
    assert by_reason == [("error",), ("negative",)] + [("uncited",)] * 3

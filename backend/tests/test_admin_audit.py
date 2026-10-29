import pytest

from app.models.domain import AdminAuditLog, User, UserRole
from app.services.admin.audit import AuditAction, record_audit
from tests.admin_support import make_user


def test_record_audit_saves_who_what_and_to_whom(client):
    _, factory = client
    admin, _ = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    target, _ = make_user(factory, email="b@example.com")
    with factory() as db:
        row = record_audit(
            db, actor_id=admin.id, action=AuditAction.USER_ROLE_CHANGED,
            target_user_id=target.id, detail={"from": "user", "to": "admin"},
        )
        db.commit()
        saved = db.get(AdminAuditLog, row.id)
        assert saved.actor_id == admin.id
        assert saved.action == "user.role_changed"
        assert saved.target_user_id == target.id
        assert saved.detail == {"from": "user", "to": "admin"}
        assert saved.created_at is not None


@pytest.mark.parametrize(
    "key",
    [
        "password", "token", "email", "question", "answer", "content",
        "Email", "EMAIL", "user_email", "new_password", "access_token", "Question_text",
    ],
)
def test_rejects_forbidden_keys_in_detail(client, key):
    _, factory = client
    admin, _ = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    with factory() as db:
        with pytest.raises(ValueError):
            record_audit(db, actor_id=admin.id, action=AuditAction.REVIEW_MARKED, detail={key: "x"})


def test_record_survives_actor_deletion(client):
    _, factory = client
    admin, _ = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    with factory() as db:
        row = record_audit(db, actor_id=admin.id, action=AuditAction.USER_DELETED, target_user_id=999)
        db.commit()
        row_id = row.id
    with factory() as db:
        db.delete(db.get(User, admin.id))
        db.commit()
    with factory() as db:
        saved = db.get(AdminAuditLog, row_id)
        assert saved is not None
        assert saved.actor_id is None
        assert saved.target_user_id == 999


def _seed_rows(factory, admin_id, other_id):
    from datetime import datetime, timedelta, timezone

    base = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    with factory() as db:
        for i, (actor, action) in enumerate(
            [
                (admin_id, AuditAction.USER_ROLE_CHANGED),
                (other_id, AuditAction.USER_DEACTIVATED),
                (admin_id, AuditAction.USER_DEACTIVATED),
            ]
        ):
            row = record_audit(db, actor_id=actor, action=action, target_user_id=7, detail={"n": i})
            row.created_at = base + timedelta(minutes=i)
        db.commit()


def test_lists_most_recent_first(client):
    http, factory = client
    admin, headers = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    other, _ = make_user(factory, email="b@example.com", role=UserRole.ADMIN)
    _seed_rows(factory, admin.id, other.id)
    body = http.get("/api/v1/admin/audit", headers=headers).json()
    assert body["total"] == 3
    assert (body["page"], body["page_size"]) == (1, 20)
    assert [r["detail"]["n"] for r in body["items"]] == [2, 1, 0]
    first = body["items"][0]
    assert first["actor_name"] == "Test User"
    assert first["action"] == "user.deactivated"
    assert first["target_user_id"] == 7
    assert set(first) == {
        "id", "created_at", "actor_name", "action", "target_user_id", "target_name", "detail",
    }
    assert first["target_name"] is None


def test_filters_by_actor_and_action(client):
    http, factory = client
    admin, headers = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    other, _ = make_user(factory, email="b@example.com", role=UserRole.ADMIN)
    _seed_rows(factory, admin.id, other.id)
    url = "/api/v1/admin/audit"
    by_actor = http.get(url, params={"actor_id": other.id}, headers=headers).json()
    assert by_actor["total"] == 1
    by_action = http.get(url, params={"action": "user.deactivated"}, headers=headers).json()
    assert by_action["total"] == 2
    both = http.get(
        url, params={"actor_id": admin.id, "action": "user.deactivated"}, headers=headers
    ).json()
    assert [r["detail"]["n"] for r in both["items"]] == [2]
    assert http.get(url, params={"action": "nope"}, headers=headers).status_code == 422


def test_actor_name_is_null_when_actor_no_longer_exists(client):
    http, factory = client
    admin, headers = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    gone, _ = make_user(factory, email="gone@example.com", role=UserRole.ADMIN)
    with factory() as db:
        record_audit(db, actor_id=gone.id, action=AuditAction.USER_DELETED, target_user_id=5)
        db.commit()
        db.delete(db.get(User, gone.id))
        db.commit()
    body = http.get("/api/v1/admin/audit", headers=headers).json()
    assert body["total"] == 1
    assert body["items"][0]["actor_name"] is None


def test_audit_pagination_bounds(client):
    http, factory = client
    _, headers = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    url = "/api/v1/admin/audit"
    assert http.get(url, params={"page": 99}, headers=headers).json()["items"] == []
    assert http.get(url, params={"page_size": 51}, headers=headers).status_code == 422
    assert http.get(url, params={"page": 0}, headers=headers).status_code == 422


def test_audit_forbidden_for_normal_user_and_anonymous(client):
    http, factory = client
    _, headers = make_user(factory, email="u@example.com")
    assert http.get("/api/v1/admin/audit", headers=headers).status_code == 403
    assert http.get("/api/v1/admin/audit").status_code == 401


@pytest.mark.parametrize("value", [{"a": 1}, ["x", "y"]])
def test_record_audit_rechaza_valores_anidados(client, value):
    _, factory = client
    admin, _ = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    with factory() as db:
        with pytest.raises(ValueError):
            record_audit(
                db, actor_id=admin.id, action=AuditAction.REVIEW_MARKED, detail={"x": value}
            )


def test_record_audit_rechaza_una_clave_prohibida_dentro_de_un_valor_anidado(client):
    _, factory = client
    admin, _ = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    with factory() as db:
        with pytest.raises(ValueError):
            record_audit(
                db,
                actor_id=admin.id,
                action=AuditAction.REVIEW_MARKED,
                detail={"x": {"Email": "a@b.mx"}},
            )


def test_la_lectura_omite_valores_no_escalares_de_una_fila_antigua(client):
    http, factory = client
    admin, headers = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    with factory() as db:
        db.add(
            AdminAuditLog(
                actor_id=admin.id,
                action="review.marked",
                target_user_id=None,
                detail={"ok": 1, "bad": {"a": 1}},
            )
        )
        db.commit()
    body = http.get("/api/v1/admin/audit", headers=headers).json()
    assert body["items"][0]["detail"] == {"ok": 1}


def test_target_name_is_present_then_null_after_the_person_is_deleted(client):
    http, factory = client
    _, headers = make_user(factory, email="a@example.com", role=UserRole.ADMIN)
    admin = make_user(factory, email="b@example.com", role=UserRole.ADMIN)[0]
    target, _ = make_user(factory, email="t@example.com")
    with factory() as db:
        person = db.get(User, target.id)
        person.first_name, person.last_name = "María", "López"
        record_audit(
            db, actor_id=admin.id, action=AuditAction.USER_DEACTIVATED, target_user_id=target.id
        )
        db.commit()
    url = "/api/v1/admin/audit"
    row = http.get(url, headers=headers).json()["items"][0]
    assert row["target_name"] == "María López"
    assert "t@example.com" not in str(row)
    with factory() as db:
        db.delete(db.get(User, target.id))
        db.commit()
    row = http.get(url, headers=headers).json()["items"][0]
    assert row["target_name"] is None
    assert row["target_user_id"] == target.id

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

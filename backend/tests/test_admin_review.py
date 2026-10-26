import pytest
from sqlalchemy.exc import IntegrityError

from app.models.domain import Conversation, Message, MessageReview, MessageRole, UserRole
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

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.core.config import Settings
from app.models.domain import ChatUsage, Conversation, Message, MessageRole, UsageStatus, User
from app.services.chat_limits import ChatLimitError, check_can_send

MX = ZoneInfo("America/Mexico_City")
NOW = datetime(2026, 10, 12, 15, 0, tzinfo=MX)  # a Monday afternoon in Mexico City


def settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


def make_user(db, email="ana@example.com") -> User:
    user = User(first_name="Ana", last_name="López", email=email, password_hash="x")
    db.add(user)
    db.flush()
    return user


def make_conversation(db, user) -> Conversation:
    conversation = Conversation(user_id=user.id)
    db.add(conversation)
    db.flush()
    return conversation


def add_messages(db, conversation, count, role=MessageRole.USER, at=NOW):
    db.add_all(Message(conversation_id=conversation.id, role=role, content="m", created_at=at) for _ in range(count))
    db.flush()


def add_usage(db, user, count, at=NOW):
    """The daily limit counts ledger rows (one per accepted turn), not stored messages."""
    db.add_all(
        ChatUsage(user_id=user.id, created_at=at, input_tokens=1, output_tokens=1, reserved_input_tokens=1,
                  reserved_output_tokens=1, status=UsageStatus.SETTLED)
        for _ in range(count)
    )
    db.flush()


def error_of(db, user, conversation, content, cfg=None) -> ChatLimitError:
    with pytest.raises(ChatLimitError) as raised:
        check_can_send(db, user.id, conversation.id, content, cfg or settings(), now=NOW)
    return raised.value


def test_a_normal_message_is_accepted_and_trimmed(client):
    _, factory = client
    with factory() as db:
        user = make_user(db)
        conversation = make_conversation(db, user)
        assert check_can_send(db, user.id, conversation.id, "  ¿me pueden multar?  ", settings(), now=NOW) == "¿me pueden multar?"


def test_an_empty_or_oversized_message_is_422(client):
    _, factory = client
    with factory() as db:
        user = make_user(db)
        conversation = make_conversation(db, user)
        empty = error_of(db, user, conversation, "   \n ")
        assert (empty.status_code, empty.code) == (422, "mensaje_vacio")
        long = error_of(db, user, conversation, "x" * 2001)
        assert (long.status_code, long.code) == (422, "mensaje_demasiado_largo")
        assert check_can_send(db, user.id, conversation.id, "x" * 2000, settings(), now=NOW)  # the limit itself is allowed


def test_a_full_conversation_is_409_counting_both_roles(client):
    _, factory = client
    with factory() as db:
        user = make_user(db)
        conversation = make_conversation(db, user)
        earlier = NOW - timedelta(days=2)  # old messages: this test is about the conversation cap, not the daily one
        add_messages(db, conversation, 100, MessageRole.USER, at=earlier)
        add_messages(db, conversation, 99, MessageRole.ASSISTANT, at=earlier)
        assert check_can_send(db, user.id, conversation.id, "hola", settings(), now=NOW)  # 199 stored: one more fits
        add_messages(db, conversation, 1, MessageRole.ASSISTANT, at=earlier)
        full = error_of(db, user, conversation, "hola")
        assert (full.status_code, full.code) == (409, "conversacion_llena")


def test_the_daily_limit_counts_only_the_users_own_messages_sent_today_in_mexico_city(client):
    _, factory = client
    with factory() as db:
        user, other = make_user(db), make_user(db, "luis@example.com")
        mine, theirs, old = make_conversation(db, user), make_conversation(db, other), make_conversation(db, user)
        midnight_mx = NOW.replace(hour=0, minute=0, second=0)

        add_usage(db, user, 30, at=NOW)                                        # today
        add_messages(db, mine, 10, MessageRole.ASSISTANT, at=NOW)              # messages themselves do not count
        add_usage(db, other, 50, at=NOW)                                       # someone else's
        add_usage(db, user, 20, at=midnight_mx - timedelta(minutes=30))        # 23:30 yesterday in Mexico City
        assert check_can_send(db, user.id, mine.id, "hola", settings(), now=NOW)

        add_usage(db, user, 10, at=midnight_mx + timedelta(minutes=1))         # reaches 40 today
        blocked = error_of(db, user, mine, "hola")
        assert (blocked.status_code, blocked.code) == (429, "limite_diario")
        assert "40" in blocked.message


def test_the_limits_are_configurable(client):
    _, factory = client
    with factory() as db:
        user = make_user(db)
        conversation = make_conversation(db, user)
        add_usage(db, user, 2)
        assert error_of(db, user, conversation, "hola", settings(chat_daily_message_limit=2)).status_code == 429
        assert error_of(db, user, conversation, "x" * 11, settings(chat_max_message_chars=10)).status_code == 422

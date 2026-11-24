import pytest

from app.core.exceptions import ConversationAccessDenied
from app.services.conversation import ConversationService


def test_new_conversation_is_owned_by_its_creator():

    service = ConversationService()

    conversation_id = service.resolve_conversation(None, user_id=1)

    assert service.resolve_conversation(conversation_id, user_id=1) == conversation_id


def test_another_user_cannot_use_the_conversation():

    service = ConversationService()

    conversation_id = service.resolve_conversation(None, user_id=1)
    service.add_user_message(conversation_id, "I'm on a performance plan.")

    with pytest.raises(ConversationAccessDenied):
        service.resolve_conversation(conversation_id, user_id=2)

    # Nothing was added to, or read from, the owner's conversation.
    assert [m.content for m in service.get_history(conversation_id)] == ["I'm on a performance plan."]


def test_unknown_conversation_id_is_claimed_by_the_caller():
    """After a restart the in-memory store is empty, and the frontend
    keeps sending the id it had - that must keep working."""

    service = ConversationService()

    assert service.resolve_conversation("id-from-before-a-restart", user_id=3) == "id-from-before-a-restart"

    with pytest.raises(ConversationAccessDenied):
        service.resolve_conversation("id-from-before-a-restart", user_id=4)


def test_swagger_placeholder_starts_a_new_conversation():

    service = ConversationService()

    conversation_id = service.resolve_conversation("string", user_id=5)

    assert conversation_id != "string"

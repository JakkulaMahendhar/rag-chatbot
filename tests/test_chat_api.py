from collections import defaultdict
from unittest.mock import AsyncMock, patch

from app.api.chat import _chat_rate_limiter
from app.core.exceptions import ConversationAccessDenied

FAKE_ANSWER = {"answer": "An answer.", "sources": [], "conversation_id": "conv-1", "search_evaluation": {}}


def test_chat_requires_auth(client):

    response = client.post("/chat", json={"question": "What is RAG?"})

    assert response.status_code == 401


def test_chat_returns_rag_service_response(client, register_user):

    user = register_user()

    fake_answer = {
        "answer": "Retrieval-Augmented Generation combines retrieval with generation.",
        "sources": [],
        "conversation_id": "conv-123",
    }

    with patch("app.api.chat.RAGChatService") as MockService:

        MockService.return_value.chat = AsyncMock(return_value=fake_answer)

        response = client.post(
            "/chat",
            json={"question": "What is RAG?"},
            headers=user["headers"],
        )

    assert response.status_code == 200
    assert response.json() == fake_answer

    _, kwargs = MockService.return_value.chat.call_args

    assert kwargs["user_id"] == user["id"]
    assert kwargs["question"] == "What is RAG?"
    assert kwargs["conversation_id"] is None


def test_other_users_conversation_returns_404(client, register_user):

    user = register_user()

    with patch("app.api.chat.RAGChatService") as MockService:

        MockService.return_value.chat = AsyncMock(
            side_effect=ConversationAccessDenied("someone-elses-conversation")
        )

        response = client.post(
            "/chat",
            json={"question": "What did I ask before?", "conversation_id": "someone-elses-conversation"},
            headers=user["headers"],
        )

    # 404, not 403: the response must not confirm the conversation exists.
    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_chat_is_rate_limited_per_user(client, register_user, monkeypatch):

    monkeypatch.setattr(_chat_rate_limiter, "max_attempts", 2)
    monkeypatch.setattr(_chat_rate_limiter, "_hits", defaultdict(list))

    alice, bob = register_user(), register_user()

    with patch("app.api.chat.RAGChatService") as MockService:

        MockService.return_value.chat = AsyncMock(return_value=FAKE_ANSWER)

        def ask(user, path="/chat"):
            return client.post(path, json={"question": "q"}, headers=user["headers"]).status_code

        # /chat and /chat/stream share one budget per user.
        assert ask(alice) == 200
        assert ask(alice, "/chat/stream") == 200
        assert ask(alice) == 429
        assert ask(alice, "/chat/stream") == 429

        # Keyed by user, not IP: Bob (same test client IP) is unaffected.
        assert ask(bob) == 200

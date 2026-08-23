from unittest.mock import AsyncMock, patch


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

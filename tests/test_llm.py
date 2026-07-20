from app.core.ai_registry import AIServiceRegistry


def test_llm_response():

    llm = AIServiceRegistry.get_llm()


    response = llm.generate(
        "Explain RAG in one sentence"
    )


    assert response is not None

    assert len(response) > 0
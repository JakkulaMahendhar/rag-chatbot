from app.core.ai_registry import AIServiceRegistry


def test_singleton():

    model1 = AIServiceRegistry.get_embedding_model()

    model2 = AIServiceRegistry.get_embedding_model()

    assert model1 is model2
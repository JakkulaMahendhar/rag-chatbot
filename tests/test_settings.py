from app.core.config import settings


def test_gemini_settings():

    assert settings.gemini_api_key is not None

    assert settings.gemini_model == "gemini-2.5-flash"

    assert settings.llm_provider == "gemini"
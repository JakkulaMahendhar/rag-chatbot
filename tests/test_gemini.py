import google.generativeai as genai

from app.core.config import settings


def test_gemini_connection():

    genai.configure( # type: ignore
        api_key=settings.gemini_api_key
    )


    model = genai.GenerativeModel( # type: ignore
        settings.gemini_model
    )


    response = model.generate_content(
        "Explain RAG in one sentence"
    )


    assert response.text is not None
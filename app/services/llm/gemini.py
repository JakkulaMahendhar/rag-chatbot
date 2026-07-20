import google.generativeai as genai

from app.core.config import settings
from app.services.llm.base import LLMService


class GeminiService(LLMService):


    def __init__(self):

        genai.configure( # type: ignore
            api_key=settings.gemini_api_key
        )


        self.model = genai.GenerativeModel( # type: ignore
            settings.gemini_model
        )


    def generate(
        self,
        prompt: str
    ) -> str:


        response = self.model.generate_content(
            prompt
        )


        return response.text
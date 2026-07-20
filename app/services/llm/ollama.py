import ollama

from app.core.config import settings
from app.services.llm.base import LLMService


class OllamaService(LLMService):


    def __init__(self):

        self.model = settings.ollama_model


    def generate(
        self,
        prompt: str
    ) -> str:


        response = ollama.chat(

            model=self.model,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]

        )


        return response["message"]["content"]
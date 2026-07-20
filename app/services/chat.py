from app.core.ai_registry import AIServiceRegistry
from app.services.prompt import PromptBuilder


class ChatService:


    def __init__(self):

        self.llm = AIServiceRegistry.get_llm()



    def answer(
        self,
        question: str,
        contexts: list[str]
    ):


        prompt = PromptBuilder.build(
            question,
            contexts
        )


        return self.llm.generate( # type: ignore
            prompt
        )
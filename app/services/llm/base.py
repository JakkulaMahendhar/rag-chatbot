from abc import ABC, abstractmethod


class LLMService(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: str
    ) -> str:
        pass
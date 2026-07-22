from abc import ABC, abstractmethod

from app.models.conversation import ConversationMessage



class ConversationStore(ABC):


    @abstractmethod
    def create(
        self,
        conversation_id: str
    ):
        pass



    @abstractmethod
    def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage
    ):
        pass



    @abstractmethod
    def get_messages(
        self,
        conversation_id: str
    ) -> list[ConversationMessage]:
        pass
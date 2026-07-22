from uuid import uuid4

from app.models.conversation import ConversationMessage

from app.services.conversation_store.memory import (
    InMemoryConversationStore
)
from app.core.logger import logger


conversation_store = InMemoryConversationStore()


class ConversationService:


    def __init__(self):

        self.store = conversation_store



    def create_conversation(
        self
    ) -> str:

        conversation_id = str(
            uuid4()
        )

        logger.info(
            f"Creating conversation: {conversation_id}"
        )

        self.store.create(
            conversation_id
        )


        return conversation_id



    def add_user_message(
        self,
        conversation_id: str,
        content: str
    ):

        self.store.add_message(

            conversation_id,

            ConversationMessage(

                role="user",

                content=content

            )
        )



    def add_assistant_message(
        self,
        conversation_id: str,
        content: str
    ):

        self.store.add_message(

            conversation_id,

            ConversationMessage(

                role="assistant",

                content=content

            )
        )



    def get_history(
        self,
        conversation_id: str
    ):

        return self.store.get_messages(
            conversation_id
        )
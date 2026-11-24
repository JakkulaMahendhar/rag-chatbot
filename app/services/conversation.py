from uuid import uuid4

from app.models.conversation import ConversationMessage

from app.services.conversation_store.memory import (
    InMemoryConversationStore
)
from app.core.exceptions import ConversationAccessDenied
from app.core.logger import logger


conversation_store = InMemoryConversationStore()


class ConversationService:


    def __init__(self):

        self.store = conversation_store



    def create_conversation(
        self,
        user_id: int | None = None
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

        if user_id is not None:

            self.store.set_owner(
                conversation_id,
                user_id
            )


        return conversation_id



    def resolve_conversation(
        self,
        conversation_id: str | None,
        user_id: int | None
    ) -> str:
        """
        Return the conversation_id this request should use, enforcing
        ownership.

        - No id (or Swagger's "string" placeholder): start a new
          conversation owned by this user.
        - An id owned by someone else: ConversationAccessDenied. Without
          this check, anyone holding another user's conversation_id
          (from a log line, a screenshot, a shared URL) got that user's
          history fed into their own query rewrite and prompt.
        - An unknown id: claim it for this user. The store is in-memory,
          so after a restart every existing id is unknown, and the
          frontend keeps sending the id it already has. The history is
          already gone at that point, so there's nothing to leak.
        """

        if not conversation_id or conversation_id == "string":

            return self.create_conversation(user_id)


        if user_id is None:

            return conversation_id


        owner = self.store.get_owner(
            conversation_id
        )

        if owner is None:

            self.store.create(
                conversation_id
            )

            self.store.set_owner(
                conversation_id,
                user_id
            )

        elif owner != user_id:

            logger.warning(
                f"Conversation access denied | "
                f"conversation_id={conversation_id} | "
                f"user_id={user_id}"
            )

            raise ConversationAccessDenied(
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
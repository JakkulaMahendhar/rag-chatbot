from app.models.conversation import ConversationMessage

from app.services.conversation_store.base import ConversationStore



class InMemoryConversationStore(
    ConversationStore
):


    def __init__(self):

        self.store = {}



    def create(
        self,
        conversation_id: str
    ):

        if conversation_id not in self.store:

            self.store[conversation_id] = []



    def add_message(
        self,
        conversation_id: str,
        message: ConversationMessage
    ):

        self.create(
            conversation_id
        )


        self.store[
            conversation_id
        ].append(
            message
        )



    def get_messages(
        self,
        conversation_id: str
    ):

        return self.store.get(
            conversation_id,
            []
        )
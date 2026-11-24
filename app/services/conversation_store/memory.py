from app.models.conversation import ConversationMessage

from app.services.conversation_store.base import ConversationStore



class InMemoryConversationStore(
    ConversationStore
):


    def __init__(self):

        self.store = {}

        # conversation_id -> user_id of whoever started it
        self.owners = {}



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



    def set_owner(
        self,
        conversation_id: str,
        user_id: int
    ):

        self.owners[conversation_id] = user_id



    def get_owner(
        self,
        conversation_id: str
    ):

        return self.owners.get(
            conversation_id
        )
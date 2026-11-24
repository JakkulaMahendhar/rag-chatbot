class DocumentProcessingException(Exception):

    def __init__(self, message: str):

        self.message = message

        super().__init__(message)


class VectorStoreException(Exception):

    def __init__(self, message: str):

        self.message = message

        super().__init__(message)


class ConversationAccessDenied(Exception):
    """A user sent a conversation_id that belongs to another user."""

    def __init__(self, conversation_id: str):

        self.conversation_id = conversation_id

        super().__init__(f"Conversation {conversation_id} belongs to another user")
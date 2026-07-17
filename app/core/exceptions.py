class DocumentProcessingException(Exception):

    def __init__(self, message: str):

        self.message = message

        super().__init__(message)


class VectorStoreException(Exception):

    def __init__(self, message: str):

        self.message = message

        super().__init__(message)
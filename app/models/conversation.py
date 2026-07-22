from datetime import datetime
from pydantic import BaseModel


class ConversationMessage(BaseModel):

    role: str

    content: str

    timestamp: datetime = datetime.utcnow()
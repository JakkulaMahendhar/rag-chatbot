from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Document(Base):

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ================================
    # Owner relationship
    # ================================

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ================================
    # Processing status
    #
    # pending    - row created, file saved, not yet processed
    # processing - a worker has picked it up
    # completed  - chunked, embedded, and indexed successfully
    # failed     - processing raised; see error_message
    # ================================

    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ================================
    # Reverse relationship
    # Document belongs to User
    # ================================

    user: Mapped["User"] = relationship("User", back_populates="documents")

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from school_assistant.models.base import Base, JSONDocument, UUIDPrimaryKeyMixin


class SeenMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "seen_messages"
    __table_args__ = (UniqueConstraint("user_id", "moodle_message_id"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    moodle_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    classification: Mapped[dict[str, object] | None] = mapped_column(JSONDocument)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

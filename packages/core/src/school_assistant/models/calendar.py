from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from school_assistant.models.base import Base, UUIDPrimaryKeyMixin


class CalendarLink(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "calendar_links"
    __table_args__ = (UniqueConstraint("user_id", "moodle_event_id"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    moodle_event_id: Mapped[str] = mapped_column(String(200), nullable=False)
    gcal_event_id: Mapped[str] = mapped_column(String(300), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    event_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

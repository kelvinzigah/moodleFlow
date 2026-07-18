from datetime import datetime, time
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Time, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from school_assistant.models.base import Base, JSONDocument, UUIDPrimaryKeyMixin


class NotificationPreference(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notification_prefs"
    __table_args__ = (UniqueConstraint("user_id"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_toggles: Mapped[dict[str, bool]] = mapped_column(
        JSONDocument, default=dict, nullable=False
    )
    quiet_hours_start: Mapped[time | None] = mapped_column(Time)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time)
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    digest_time: Mapped[time | None] = mapped_column(Time)
    paused_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NotificationLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notification_log"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONDocument, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    telegram_message_id: Mapped[str | None] = mapped_column(String(100))

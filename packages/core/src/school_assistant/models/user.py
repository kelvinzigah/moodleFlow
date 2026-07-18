from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from school_assistant.models.base import (
    Base,
    JSONDocument,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    invite_code_used: Mapped[str | None] = mapped_column(String(100))
    school_calendar_id: Mapped[str | None] = mapped_column(String(300))
    drive_root_folder_id: Mapped[str | None] = mapped_column(String(300))
    drive_root_folder_name: Mapped[str] = mapped_column(
        String(200), default="School Assistant", nullable=False
    )
    notion_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class OAuthCredential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "oauth_credentials"
    __table_args__ = (UniqueConstraint("user_id", "provider"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    refresh_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSONDocument, default=list, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MoodleAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "moodle_accounts"
    __table_args__ = (UniqueConstraint("user_id"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    ws_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    capabilities: Mapped[dict[str, object]] = mapped_column(
        JSONDocument, default=dict, nullable=False
    )
    last_ok_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TelegramLink(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "telegram_links"
    __table_args__ = (UniqueConstraint("user_id"), UniqueConstraint("chat_id"))

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chat_id: Mapped[str] = mapped_column(String(100), nullable=False)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InviteCode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "invite_codes"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    claimed_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from school_assistant.models.base import Base, UUIDPrimaryKeyMixin


class FileLedgerEntry(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "file_ledger"
    __table_args__ = (
        UniqueConstraint("user_id", "moodle_file_url"),
        ForeignKeyConstraint(
            ["user_id", "course_id"],
            ["courses.user_id", "courses.id"],
            name="fk_file_ledger_course_owner",
            ondelete="CASCADE",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    course_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    moodle_file_url: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    timemodified: Mapped[int | None] = mapped_column(BigInteger)
    filesize: Mapped[int | None] = mapped_column(BigInteger)
    drive_file_id: Mapped[str] = mapped_column(String(300), nullable=False)
    drive_path: Mapped[str] = mapped_column(Text, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

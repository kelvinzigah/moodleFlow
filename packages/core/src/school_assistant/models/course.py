from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from school_assistant.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Course(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("user_id", "moodle_course_id"),
        UniqueConstraint("user_id", "id", name="uq_courses_user_id_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    moodle_course_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    course_code: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    is_tracked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    drive_folder_id: Mapped[str | None] = mapped_column(String(300))


class CoursePreference(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "course_prefs"
    __table_args__ = (
        UniqueConstraint("course_id"),
        ForeignKeyConstraint(
            ["user_id", "course_id"],
            ["courses.user_id", "courses.id"],
            name="fk_course_prefs_course_owner",
            ondelete="CASCADE",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    course_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    calendar_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    files_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    messages_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    drive_folder_override: Mapped[str | None] = mapped_column(String(300))

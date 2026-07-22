import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from school_assistant.db import SessionFactory
from school_assistant.models import Course, SeenMessage


@dataclass(frozen=True)
class ImportResult:
    messages_imported: int
    courses_imported: int


@dataclass(frozen=True)
class LegacyStateSummary:
    seen_messages: int
    courses: int


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Legacy state file does not exist: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


async def import_legacy_state(
    sessions: SessionFactory,
    user_id: UUID,
    *,
    seen_ids_path: Path,
    course_ids_path: Path,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> ImportResult:
    raw_message_ids = _read_json(seen_ids_path)
    raw_courses = _read_json(course_ids_path)
    message_ids = {int(value) for value in raw_message_ids}

    async with sessions() as session:
        existing_message_ids = set(
            await session.scalars(
                select(SeenMessage.moodle_message_id).where(SeenMessage.user_id == user_id)
            )
        )
        existing_course_ids = set(
            await session.scalars(select(Course.moodle_course_id).where(Course.user_id == user_id))
        )

        new_message_ids = message_ids - existing_message_ids
        for message_id in new_message_ids:
            session.add(
                SeenMessage(
                    user_id=user_id,
                    moodle_message_id=message_id,
                    classification={"source": "legacy_import"},
                    processed_at=clock(),
                )
            )

        courses_imported = 0
        for raw_id, raw_details in raw_courses.items():
            moodle_course_id = int(raw_id)
            if moodle_course_id in existing_course_ids:
                continue
            details = raw_details if isinstance(raw_details, dict) else {}
            course_code = str(details.get("course_code") or "unknown")
            status = str(details.get("status") or "pending")
            name = course_code if course_code != "unknown" else f"Moodle course {moodle_course_id}"
            session.add(
                Course(
                    user_id=user_id,
                    moodle_course_id=moodle_course_id,
                    course_code=None if course_code == "unknown" else course_code,
                    name=name,
                    status=status,
                    is_tracked=status == "active",
                )
            )
            courses_imported += 1

        await session.commit()
        return ImportResult(
            messages_imported=len(new_message_ids), courses_imported=courses_imported
        )


async def get_legacy_state_summary(sessions: SessionFactory, user_id: UUID) -> LegacyStateSummary:
    async with sessions() as session:
        seen_messages = await session.scalar(
            select(func.count()).select_from(SeenMessage).where(SeenMessage.user_id == user_id)
        )
        courses = await session.scalar(
            select(func.count()).select_from(Course).where(Course.user_id == user_id)
        )
        return LegacyStateSummary(seen_messages=seen_messages or 0, courses=courses or 0)

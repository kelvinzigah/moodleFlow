import json
from datetime import UTC, datetime

import pytest
from school_assistant.db import Base
from school_assistant.legacy_state import get_legacy_state_summary, import_legacy_state
from school_assistant.models import User
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_legacy_state_import_is_idempotent(tmp_path) -> None:  # type: ignore[no-untyped-def]
    seen_ids_path = tmp_path / "seen_ids.json"
    course_ids_path = tmp_path / "seen_moodle_course_ids.json"
    seen_ids_path.write_text(json.dumps([101, 102]), encoding="utf-8")
    course_ids_path.write_text(
        json.dumps(
            {
                "12345": {"course_code": "ELEC 273", "status": "active"},
                "67890": {"course_code": "unknown", "status": "ignored"},
            }
        ),
        encoding="utf-8",
    )
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        user = User(email="owner@example.com", display_name="Owner")
        session.add(user)
        await session.commit()
        await session.refresh(user)

    now = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)
    first = await import_legacy_state(
        sessions,
        user.id,
        seen_ids_path=seen_ids_path,
        course_ids_path=course_ids_path,
        clock=lambda: now,
    )
    second = await import_legacy_state(
        sessions,
        user.id,
        seen_ids_path=seen_ids_path,
        course_ids_path=course_ids_path,
        clock=lambda: now,
    )
    persisted = await get_legacy_state_summary(sessions, user.id)

    assert first.messages_imported == 2
    assert first.courses_imported == 2
    assert second.messages_imported == 0
    assert second.courses_imported == 0
    assert persisted.seen_messages == 2
    assert persisted.courses == 2

    await engine.dispose()


@pytest.mark.asyncio
async def test_legacy_state_import_fails_when_a_source_file_is_missing(tmp_path) -> None:  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    with pytest.raises(FileNotFoundError, match="seen_ids.json"):
        await import_legacy_state(
            sessions,
            User(email="unused@example.com").id,
            seen_ids_path=tmp_path / "seen_ids.json",
            course_ids_path=tmp_path / "seen_moodle_course_ids.json",
        )

    await engine.dispose()

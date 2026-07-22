from datetime import UTC, datetime

import pytest
from school_assistant.db import Base
from school_assistant.job_runs import get_latest_job_run
from school_assistant.models import CoursePreference, FileLedgerEntry, JobRun, User
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_job_run_lookup_is_scoped_to_its_user() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    started_at = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)

    async with sessions() as session:
        first_user = User(email="first@example.com")
        second_user = User(email="second@example.com")
        session.add_all([first_user, second_user])
        await session.flush()
        session.add_all(
            [
                JobRun(
                    user_id=first_user.id,
                    job_name="messages",
                    started_at=started_at,
                    outcome="succeeded",
                ),
                JobRun(
                    user_id=second_user.id,
                    job_name="messages",
                    started_at=started_at,
                    outcome="failed",
                ),
            ]
        )
        await session.commit()

    latest = await get_latest_job_run(sessions, first_user.id, "messages")

    assert latest is not None
    assert latest.outcome == "succeeded"
    await engine.dispose()


def test_course_children_enforce_matching_tenant_and_course() -> None:
    for table in (CoursePreference.__table__, FileLedgerEntry.__table__):
        composite_owners = [
            constraint
            for constraint in table.foreign_key_constraints
            if tuple(constraint.column_keys) == ("user_id", "course_id")
        ]

        assert len(composite_owners) == 1
        assert {element.target_fullname for element in composite_owners[0].elements} == {
            "courses.user_id",
            "courses.id",
        }

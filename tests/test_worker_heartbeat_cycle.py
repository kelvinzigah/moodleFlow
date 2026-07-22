from datetime import UTC, datetime

import pytest
from school_assistant.db import Base
from school_assistant.job_runs import get_latest_worker_heartbeat, run_heartbeat_cycle
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_worker_cycle_records_successful_heartbeat() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sessions = async_sessionmaker(engine, expire_on_commit=False)
    observed_at = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)

    result = await run_heartbeat_cycle(sessions, clock=lambda: observed_at)
    latest = await get_latest_worker_heartbeat(sessions)

    assert result.worker_name == "scheduler"
    assert latest is not None
    assert latest.worker_name == "scheduler"
    assert latest.observed_at == observed_at

    await engine.dispose()

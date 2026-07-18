from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from school_assistant.db import SessionFactory
from school_assistant.models import JobRun, WorkerHeartbeat


@dataclass(frozen=True)
class JobRunView:
    id: UUID
    job_name: str
    started_at: datetime
    finished_at: datetime | None
    outcome: str
    error: str | None
    items_processed: int


@dataclass(frozen=True)
class WorkerHeartbeatView:
    id: UUID
    worker_name: str
    observed_at: datetime


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _heartbeat_to_view(heartbeat: WorkerHeartbeat) -> WorkerHeartbeatView:
    return WorkerHeartbeatView(
        id=heartbeat.id,
        worker_name=heartbeat.worker_name,
        observed_at=_as_utc(heartbeat.observed_at),  # type: ignore[arg-type]
    )


async def run_heartbeat_cycle(
    sessions: SessionFactory,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> WorkerHeartbeatView:
    heartbeat = WorkerHeartbeat(worker_name="scheduler", observed_at=clock())
    async with sessions() as session:
        session.add(heartbeat)
        await session.commit()
        await session.refresh(heartbeat)
        return _heartbeat_to_view(heartbeat)


async def get_latest_worker_heartbeat(
    sessions: SessionFactory, worker_name: str = "scheduler"
) -> WorkerHeartbeatView | None:
    statement = (
        select(WorkerHeartbeat)
        .where(WorkerHeartbeat.worker_name == worker_name)
        .order_by(WorkerHeartbeat.observed_at.desc())
        .limit(1)
    )
    async with sessions() as session:
        heartbeat = await session.scalar(statement)
        return _heartbeat_to_view(heartbeat) if heartbeat is not None else None


async def get_latest_job_run(
    sessions: SessionFactory, user_id: UUID, job_name: str
) -> JobRunView | None:
    statement = (
        select(JobRun)
        .where(JobRun.user_id == user_id, JobRun.job_name == job_name)
        .order_by(JobRun.started_at.desc())
        .limit(1)
    )
    async with sessions() as session:
        run = await session.scalar(statement)
        if run is None:
            return None
        return JobRunView(
            id=run.id,
            job_name=run.job_name,
            started_at=_as_utc(run.started_at),  # type: ignore[arg-type]
            finished_at=_as_utc(run.finished_at),
            outcome=run.outcome,
            error=run.error,
            items_processed=run.items_processed,
        )

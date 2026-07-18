import asyncio
import signal
from contextlib import suppress

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from school_assistant.config import get_settings
from school_assistant.db import create_engine, create_session_factory
from school_assistant.job_runs import run_heartbeat_cycle

logger = structlog.get_logger()


async def run_worker() -> None:
    settings = get_settings()
    engine = create_engine(settings)
    sessions = create_session_factory(engine)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(signum, stop_event.set)

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_heartbeat_cycle,
        "interval",
        seconds=settings.heartbeat_interval_seconds,
        kwargs={"sessions": sessions},
        id="heartbeat",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    try:
        result = await run_heartbeat_cycle(sessions)
        logger.info("startup_heartbeat", job_run_id=str(result.id))
        scheduler.start()
        await stop_event.wait()
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await engine.dispose()


def main() -> None:
    with suppress(KeyboardInterrupt):
        asyncio.run(run_worker())


if __name__ == "__main__":
    main()

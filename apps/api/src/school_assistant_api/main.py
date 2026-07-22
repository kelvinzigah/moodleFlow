from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from school_assistant.config import get_settings
from school_assistant.db import SessionFactory, create_engine, create_session_factory
from sqlalchemy import text


def create_app(
    sessions: SessionFactory,
    *,
    cors_origins: list[str] | None = None,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    app = FastAPI(title="School Assistant API", lifespan=lifespan)
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        async with sessions() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "service": "api", "database": "ready"}

    return app


def create_runtime_app() -> FastAPI:
    settings = get_settings()
    engine = create_engine(settings)
    sessions = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await engine.dispose()

    app = create_app(
        sessions,
        cors_origins=settings.cors_origins,
        lifespan=lifespan,
    )
    app.state.database_engine = engine
    return app

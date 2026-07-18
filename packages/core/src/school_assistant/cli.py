import argparse
import asyncio
from pathlib import Path

from sqlalchemy import select

from school_assistant.config import get_settings
from school_assistant.db import create_engine, create_session_factory
from school_assistant.legacy_state import import_legacy_state
from school_assistant.models import User


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="school-assistant")
    subcommands = parser.add_subparsers(dest="command", required=True)

    owner = subcommands.add_parser("create-owner")
    owner.add_argument("--email", required=True)
    owner.add_argument("--display-name", default="Owner")

    import_state = subcommands.add_parser("import-legacy-state")
    import_state.add_argument("--user-email", required=True)
    import_state.add_argument("--seen-ids", type=Path, default=Path("data/seen_ids.json"))
    import_state.add_argument(
        "--course-ids", type=Path, default=Path("data/seen_moodle_course_ids.json")
    )
    return parser


async def run_command(args: argparse.Namespace) -> None:
    settings = get_settings()
    engine = create_engine(settings)
    sessions = create_session_factory(engine)
    try:
        if args.command == "create-owner":
            async with sessions() as session:
                existing = await session.scalar(select(User).where(User.email == args.email))
                if existing is None:
                    session.add(User(email=args.email, display_name=args.display_name))
                    await session.commit()
                    print(f"Created owner {args.email}")
                else:
                    print(f"Owner already exists: {args.email}")
        elif args.command == "import-legacy-state":
            async with sessions() as session:
                user = await session.scalar(select(User).where(User.email == args.user_email))
            if user is None:
                raise SystemExit(f"Owner does not exist: {args.user_email}")
            result = await import_legacy_state(
                sessions,
                user.id,
                seen_ids_path=args.seen_ids,
                course_ids_path=args.course_ids,
            )
            print(
                f"Imported {result.messages_imported} messages and "
                f"{result.courses_imported} courses"
            )
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(run_command(build_parser().parse_args()))


if __name__ == "__main__":
    main()

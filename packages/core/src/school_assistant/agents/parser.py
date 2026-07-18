from typing import Any, cast


def parse_message(subject: str, body: str) -> dict[str, Any] | None:
    from agents.parser import parse_message as legacy_parse_message

    return cast(dict[str, Any] | None, legacy_parse_message(subject, body))

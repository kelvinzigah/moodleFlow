from typing import Any


def get_messages() -> tuple[dict[str, Any], str | None]:
    from connectors.moodle import get_messages as legacy_get_messages

    return legacy_get_messages()


def strip_html(value: str) -> str:
    from connectors.moodle import strip_html as legacy_strip_html

    return legacy_strip_html(value)

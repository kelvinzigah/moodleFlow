from typing import cast


def get_updates(offset: int = 0) -> list[dict[str, object]]:
    from connectors.telegram import get_updates as legacy_get_updates

    return cast(list[dict[str, object]], legacy_get_updates(offset))


def send(text: str) -> None:
    from connectors.telegram import send as legacy_send

    legacy_send(text)

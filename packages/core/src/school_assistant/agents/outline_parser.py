from typing import Any, cast


def parse_outline(pdf_path: str) -> dict[str, Any]:
    from agents.outline_parser import parse_outline as legacy_parse_outline

    return cast(dict[str, Any], legacy_parse_outline(pdf_path))

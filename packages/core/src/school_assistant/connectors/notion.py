from typing import Any, cast


def find_class_by_moodle_id(moodle_course_id: int) -> Any:
    from connectors.notion import find_class_by_moodle_id as legacy_find

    return legacy_find(moodle_course_id)


def find_class_by_course_code(course_code: str) -> Any:
    from connectors.notion import find_class_by_course_code as legacy_find

    return legacy_find(course_code)


def create_class(
    course_code: str,
    name: str,
    moodle_course_id: int | None = None,
    professor: str | None = None,
    credits: int | None = None,
    office_hours: str | None = None,
    textbooks: str | None = None,
) -> Any:
    from connectors.notion import create_class as legacy_create

    legacy_create_untyped = cast(Any, legacy_create)
    return legacy_create_untyped(
        course_code,
        name,
        moodle_course_id,
        professor,
        credits,
        office_hours,
        textbooks,
    )


def find_topic_by_name(name: str, class_page_id: str) -> Any:
    from connectors.notion import find_topic_by_name as legacy_find

    return legacy_find(name, class_page_id)


def create_topic(
    name: str,
    class_page_id: str,
    week_taught: list[str] | None = None,
    exam_relevance: str | None = None,
    textbook_section: str | None = None,
) -> Any:
    from connectors.notion import create_topic as legacy_create

    legacy_create_untyped = cast(Any, legacy_create)
    return legacy_create_untyped(
        name,
        class_page_id,
        week_taught,
        exam_relevance,
        textbook_section,
    )


def find_assignment_by_name(name: str, class_page_id: str) -> Any:
    from connectors.notion import find_assignment_by_name as legacy_find

    return legacy_find(name, class_page_id)


def create_assignment(
    parsed: dict[str, Any],
    subject: str,
    class_page_id: str | None = None,
    status: str = "To Do",
) -> Any:
    from connectors.notion import create_assignment as legacy_create

    return legacy_create(parsed, subject, class_page_id, status)  # type: ignore[no-untyped-call]

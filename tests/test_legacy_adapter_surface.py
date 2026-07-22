from school_assistant.agents.outline_parser import parse_outline
from school_assistant.agents.parser import parse_message
from school_assistant.connectors.moodle import get_messages, strip_html
from school_assistant.connectors.notion import (
    create_assignment,
    create_class,
    create_topic,
    find_assignment_by_name,
    find_class_by_course_code,
    find_class_by_moodle_id,
    find_topic_by_name,
)
from school_assistant.connectors.telegram import get_updates, send


def test_legacy_adapter_surface_imports_through_shared_core() -> None:
    public_functions = (
        parse_outline,
        parse_message,
        get_messages,
        strip_html,
        create_assignment,
        create_class,
        create_topic,
        find_assignment_by_name,
        find_class_by_course_code,
        find_class_by_moodle_id,
        find_topic_by_name,
        get_updates,
        send,
    )

    assert all(callable(function) for function in public_functions)
    assert strip_html("<p>portable</p>") == "portable"

import sys
import html

from agents.outline_parser import parse_outline
from connectors.notion import (
    find_class_by_course_code,
    create_class,
    find_topic_by_name,
    create_topic,
    find_assignment_by_name,
    create_assignment,
)
from connectors.telegram import send as send_telegram


def process(pdf_path: str):
    # 1. Extract all data from PDF via Claude
    print(f"Parsing outline: {pdf_path}")
    data = parse_outline(pdf_path)
    cls = data["class"]
    topics_raw = data.get("topics", [])
    assignments_raw = data.get("assignments", [])

    # 2. Class — find existing or create
    class_page_id = find_class_by_course_code(cls["course_code"])
    class_created = False
    if not class_page_id:
        create_class(
            course_code=cls["course_code"],
            name=cls["name"],
            professor=cls.get("professor"),
            credits=cls.get("credits"),
            office_hours=cls.get("office_hours"),
            textbooks=cls.get("textbooks"),
        )
        class_page_id = find_class_by_course_code(cls["course_code"])
        class_created = True

    if not class_page_id:
        send_telegram(f"❌ Failed to create or find class {cls['course_code']} in Notion.")
        return

    # 3. Topics — dedup by name + class
    topics_created, topics_skipped = [], []
    for t in topics_raw:
        existing = find_topic_by_name(t["name"], class_page_id)
        if existing:
            topics_skipped.append(t["name"])
        else:
            create_topic(
                name=t["name"],
                class_page_id=class_page_id,
                week_taught=t.get("week_taught"),
                exam_relevance=t.get("exam_relevance"),
                textbook_section=t.get("textbook_section"),
            )
            topics_created.append(t)

    # 4. Assignments — dedup by name + class, Status="Tentative"
    assignments_created, assignments_skipped = [], []
    hours_map = {"lab": 4, "exam": 7, "homework": 1, "quiz": 1, "project": 12, "assignment": 1}
    for a in assignments_raw:
        existing = find_assignment_by_name(a["name"], class_page_id)
        if existing:
            assignments_skipped.append(a["name"])
            continue
        parsed_dict = {
            "task_type": a.get("type", "other"),
            "due_date": a.get("due_date"),
            "due_time": None,
            "urgency": 2,
            "summary": "",
            "suggested_topics": a.get("suggested_topics"),
            "estimated_hours": hours_map.get((a.get("type") or "").lower()),
        }
        create_assignment(parsed_dict, a["name"], class_page_id, status="Tentative")
        assignments_created.append(a)

    # 5. Send Telegram summary
    _send_summary(cls, class_created, topics_created, topics_skipped,
                  assignments_created, assignments_skipped)


def _send_summary(cls, class_created, topics_created, topics_skipped,
                  assignments_created, assignments_skipped):
    lines = [f"📚 <b>Course outline processed: {html.escape(cls['course_code'])}</b>\n"]

    if class_created:
        lines.append(f"🏛️ <b>Class created:</b> {html.escape(cls['course_code'])} — {html.escape(cls['name'] or '')}")
    else:
        lines.append(f"🏛️ Class already exists: {html.escape(cls['course_code'])}")
    if cls.get("professor"):
        credit_str = f" | {cls['credits']} credits" if cls.get("credits") else ""
        lines.append(f"👤 {html.escape(cls['professor'])}{credit_str}")

    lines.append(f"\n📌 <b>Topics: {len(topics_created)} created, {len(topics_skipped)} skipped</b>")
    for t in topics_created:
        weeks = ", ".join(t.get("week_taught") or []) or "?"
        rel = t.get("exam_relevance") or "?"
        lines.append(f"  • {html.escape(t['name'])} (Week {weeks}, {rel})")

    lines.append(f"\n📋 <b>Assessments: {len(assignments_created)} created, {len(assignments_skipped)} skipped</b>")
    for a in assignments_created:
        due = a.get("due_date") or "TBD"
        lines.append(f"  • {html.escape(a['name'])} ({a.get('type', '?')}, {due})")

    send_telegram("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_outline.py /path/to/outline.pdf")
        sys.exit(1)
    process(sys.argv[1])

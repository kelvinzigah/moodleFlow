import re
import html
import json
import schedule
import time
from core.state import load_seen_ids, save_seen_ids, load_seen_course_ids, save_seen_course_ids
from connectors.moodle import get_messages
from connectors.telegram import send as send_telegram, get_updates
from connectors.notion import find_class_by_moodle_id, find_class_by_course_code, create_assignment, create_class
from agents.parser import parse_message


def strip_html(text):
    return re.sub(r'<[^>]+>', '', text)


# ── Telegram command handlers ─────────────────────────────────────────────────

def handle_addcourse(text, seen_course_ids):
    """
    /addcourse MOODLE_ID | COURSE_CODE | Course Name | Professor (opt) | Credits (opt)
    Example: /addcourse 12345 | ELEC 273 | Fundamentals of Electric Circuits | Dr. Emami | 3
    """
    parts = [p.strip() for p in text[len("/addcourse"):].strip().split("|")]
    if len(parts) < 3 or not parts[0].isdigit():
        send_telegram(
            "⚠️ Usage:\n"
            "<code>/addcourse MOODLE_ID | COURSE_CODE | Course Name | Professor | Credits</code>\n\n"
            "Example:\n"
            "<code>/addcourse 12345 | ELEC 273 | Fundamentals of Electric Circuits | Dr. Emami | 3</code>"
        )
        return

    moodle_id   = int(parts[0])
    course_code = parts[1]
    name        = parts[2]
    professor   = parts[3] if len(parts) > 3 else None
    credits     = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else None

    if find_class_by_moodle_id(moodle_id):
        send_telegram(f"ℹ️ Course {html.escape(course_code)} (ID {moodle_id}) already exists in Notion.")
        return

    url = create_class(course_code, name, moodle_course_id=moodle_id, professor=professor, credits=credits)
    key = str(moodle_id)
    if key in seen_course_ids:
        seen_course_ids[key]["status"] = "active"
        save_seen_course_ids(seen_course_ids)

    if url:
        send_telegram(
            f"✅ <b>Class created:</b> {html.escape(course_code)} — {html.escape(name)}\n"
            f"<a href=\"{url}\">Open in Notion</a>"
        )
    else:
        send_telegram(f"❌ Failed to create class for {html.escape(course_code)}. Check logs.")


def handle_ignorecourse(text, seen_course_ids):
    """
    /ignorecourse MOODLE_ID
    Marks a course as ignored — all future messages from it are silently skipped.
    """
    moodle_id_str = text[len("/ignorecourse"):].strip()
    if not moodle_id_str.isdigit():
        send_telegram("⚠️ Usage: <code>/ignorecourse MOODLE_ID</code>")
        return
    if moodle_id_str not in seen_course_ids:
        seen_course_ids[moodle_id_str] = {"course_code": "unknown", "status": "ignored"}
    else:
        seen_course_ids[moodle_id_str]["status"] = "ignored"
    save_seen_course_ids(seen_course_ids)
    send_telegram(f"🚫 Course ID {moodle_id_str} marked as ignored. All future messages from this course will be skipped.")


def handle_commands(tg_offset, seen_course_ids):
    updates = get_updates(tg_offset)
    for update in updates:
        tg_offset = update["update_id"] + 1
        text = update.get("message", {}).get("text", "").strip()
        if text.startswith("/addcourse"):
            handle_addcourse(text, seen_course_ids)
        elif text.startswith("/ignorecourse"):
            handle_ignorecourse(text, seen_course_ids)
    return tg_offset


# ── Main pipeline ─────────────────────────────────────────────────────────────

def main():
    seen_ids = load_seen_ids()
    seen_course_ids = load_seen_course_ids()
    data, error = get_messages()

    if error:
        send_telegram(f"⚠️ Moodle fetch failed:\n{error}")
        return

    messages = data.get("messages", [])

    if not messages:
        print("No new messages.")
        return

    new_count = 0

    for msg in messages:
        msg_id = msg.get("id")
        if msg_id in seen_ids:
            continue

        subject = msg.get("subject", "—")
        body = strip_html(msg.get("text", "")).strip()

        # 1. Send raw Telegram notification
        send_telegram(
            f"📬 <b>New Moodle Message</b>\n"
            f"From: {html.escape(msg.get('userfromfullname', 'Unknown'))}\n"
            f"Subject: {html.escape(subject)}\n\n"
            f"{body[:300]}"
        )

        # 2. AI parsing
        try:
            parsed = parse_message(subject, body)
            print(f"Parsed: {parsed}")
        except Exception as e:
            print(f"AI parsing failed: {e}")
            parsed = None

        # 3. Extract Moodle course ID from message customdata
        try:
            moodle_course_id = json.loads(msg.get("customdata", "{}")).get("courseid")
        except (json.JSONDecodeError, AttributeError):
            moodle_course_id = None

        # 4. Course detection
        if moodle_course_id is not None:
            key = str(moodle_course_id)
            course_code_hint = (parsed.get("course_code") if parsed else None) or "unknown"

            if key not in seen_course_ids:
                seen_course_ids[key] = {"course_code": course_code_hint, "status": "pending"}
                save_seen_course_ids(seen_course_ids)
                send_telegram(
                    f"🆕 <b>New Moodle course detected</b>\n"
                    f"Moodle Course ID: <code>{moodle_course_id}</code>\n"
                    f"Detected course code: {html.escape(course_code_hint)}\n"
                    f"From: <i>{html.escape(subject)}</i>\n\n"
                    f"To add to Notion:\n"
                    f"<code>/addcourse {moodle_course_id} | {course_code_hint} | Full Course Name | Professor | Credits</code>\n\n"
                    f"To ignore all future messages from this course:\n"
                    f"<code>/ignorecourse {moodle_course_id}</code>"
                )
            elif seen_course_ids[key].get("status") == "ignored":
                if msg_id is not None:
                    seen_ids.add(msg_id)
                new_count += 1
                continue
        else:
            print(f"No moodle_course_id found in message {msg_id} — skipping course tracking.")

        # 5. Assignment creation
        if parsed and parsed.get("is_assignment"):
            class_page_id = None
            if moodle_course_id:
                class_page_id = find_class_by_moodle_id(moodle_course_id)
            if class_page_id is None and parsed.get("course_code"):
                class_page_id = find_class_by_course_code(parsed["course_code"])

            if class_page_id is None:
                send_telegram(
                    f"⚠️ <b>Class not found in Notion</b>\n"
                    f"Course: {html.escape(parsed.get('course_code', '—'))} (Moodle ID: {moodle_course_id or '?'})\n"
                    f"Subject: <i>{html.escape(subject)}</i>\n\n"
                    f"Use <code>/addcourse</code> to create the class first."
                )
                if msg_id is not None:
                    seen_ids.add(msg_id)
                new_count += 1
                continue

            notion_url = create_assignment(parsed, subject, class_page_id)

            notion_link = f'\n<a href="{notion_url}">View in Notion</a>' if notion_url else ""
            send_telegram(
                f"📝 <b>Assignment logged</b>\n"
                f"<b>{html.escape(subject)}</b>\n"
                f"Course: {parsed.get('course_code', '—')}\n"
                f"Due: {parsed.get('due_date')} at {parsed.get('due_time') or '23:59'}\n"
                f"Type: {parsed.get('task_type', '—')} | Urgency: {parsed.get('urgency')}/5\n"
                f"{parsed.get('summary', '')}"
                f"{notion_link}"
            )

        if msg_id is not None:
            seen_ids.add(msg_id)
        new_count += 1

    save_seen_ids(seen_ids)
    print(f"Processed {new_count} new messages.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tg_offset = 0
    seen_course_ids = load_seen_course_ids()
    main()
    schedule.every(20).minutes.do(main)
    while True:
        schedule.run_pending()
        tg_offset = handle_commands(tg_offset, seen_course_ids)
        time.sleep(60)

import html
import schedule
import time

from core.state import load_seen_ids, save_seen_ids
from connectors import moodle, telegram, google_calendar
from agents import parser


def main():
    calendar_service = google_calendar.get_service()
    data, error = moodle.get_messages()

    if "messages" not in data:
        telegram.send("⚠️ Moodle fetch failed:\n" + (error or str(data)))
        return

    messages = data["messages"]
    if not messages:
        print("No messages found.")
        return

    seen_ids = load_seen_ids()
    new_count = 0

    for msg in messages:
        msg_id = msg.get("id")
        if msg_id in seen_ids:
            continue

        subject = msg.get("subject", "—")
        body = moodle.strip_html(msg.get("text", "")).strip()

        header = (
            f"📬 <b>New Moodle Message</b>\n"
            f"From: {html.escape(msg.get('userfromfullname', 'Unknown'))}\n"
            f"Subject: {html.escape(subject)}\n"
            f"Body:\n"
        )
        telegram.send(header + body[:4096 - len(header)])
        print(f"Sent: {subject}")

        if msg_id is not None:
            seen_ids.add(msg_id)
        new_count += 1

        try:
            parsed = parser.parse_message(subject, body)
            print(f"Parsed: {parsed}")
        except Exception as e:
            print(f"AI parsing failed: {e}")
            parsed = None

        if parsed:
            event_link = google_calendar.create_event(calendar_service, parsed, subject)
            if event_link:
                telegram.send(
                    f"📅 <b>Deadline added to Google Calendar</b>\n"
                    f"<b>{html.escape(subject)}</b>\n"
                    f"Due: {parsed.get('due_date')} at {parsed.get('due_time') or '23:59'}\n"
                    f"Type: {parsed.get('task_type', '—')} | Urgency: {parsed.get('urgency')}/5\n"
                    f"<a href='{event_link}'>View event</a>"
                )

    save_seen_ids(seen_ids)
    if new_count == 0:
        print("No new messages.")


if __name__ == "__main__":
    main()
    schedule.every(20).minutes.do(main)
    while True:
        schedule.run_pending()
        time.sleep(60)

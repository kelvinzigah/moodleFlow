import re
import json
import html
import requests
import os
import schedule
import time

from dotenv import load_dotenv

load_dotenv()

SEEN_IDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_ids.json")

MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
MOODLE_URL = os.getenv("MOODLE_URL")
USER_ID = os.getenv("MOODLE_USER_ID")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID")


def load_seen_ids():
    if os.path.exists(SEEN_IDS_FILE):
        with open(SEEN_IDS_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen_ids(seen_ids):
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(seen_ids), f)


def strip_html(text):
    return re.sub(r'<[^>]+>', '', text)


def get_moodle_messages():
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_message_get_messages",
        "moodlewsrestformat": "json",
        "useridto": USER_ID,
        "newestfirst": 1,
        "limitnum": 10,
    }
    try:
        r = requests.get(f"{MOODLE_URL}/webservice/rest/server.php", params=params, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.RequestException as e:
        msg = f"Moodle request failed: {e}"
        print(msg)
        return {}, msg
    except ValueError:
        msg = f"Moodle returned non-JSON response: {r.text[:200]}"
        print(msg)
        return {}, msg


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"}, timeout=10)
        r.raise_for_status()
        result = r.json()
        if not result.get("ok"):
            print(f"Telegram error: {result.get('description')}")
    except requests.exceptions.RequestException as e:
        print(f"Telegram request failed: {e}")


def main():
    data, error = get_moodle_messages()

    if "messages" not in data:
        send_telegram("⚠️ Moodle fetch failed:\n" + (error or str(data)))
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

        header = (
            f"📬 <b>New Moodle Message</b>\n"
            f"From: {html.escape(msg.get('userfromfullname', 'Unknown'))}\n"
            f"Subject: {html.escape(msg.get('subject', '—'))}\n"
            f"Body:\n"
        )
        body = strip_html(msg.get("text", "")).strip()
        text = header + body[:4096 - len(header)]
        send_telegram(text)
        print(f"Sent: {msg.get('subject')}")
        if msg_id is not None:
            seen_ids.add(msg_id)
        new_count += 1

    save_seen_ids(seen_ids)
    if new_count == 0:
        print("No new messages.")


if __name__ == "__main__":
    main()  # run once immediately on start
    schedule.every(20).minutes.do(main)
    while True:
        schedule.run_pending()
        time.sleep(60)
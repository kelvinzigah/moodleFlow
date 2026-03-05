import requests
import os
from dotenv import load_dotenv

load_dotenv()

MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
MOODLE_URL = os.getenv("MOODLE_URL")
USER_ID = os.getenv("MOODLE_USER_ID")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID")


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
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"Moodle request failed: {e}")
        return {}
    except ValueError:
        print(f"Moodle returned non-JSON response: {r.text[:200]}")
        return {}


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
    data = get_moodle_messages()

    if "messages" not in data:
        send_telegram("⚠️ Moodle fetch failed:\n" + str(data))
        return

    messages = data["messages"]
    if not messages:
        print("No messages found.")
        return

    for msg in messages:
        text = (
            f"📬 <b>New Moodle Message</b>\n"
            f"From: {msg.get('userfromfullname', 'Unknown')}\n"
            f"Subject: {msg.get('subject', '—')}\n"
            f"Preview: {msg.get('text', '')[:200]}"
        )
        send_telegram(text)
        print(f"Sent: {msg.get('subject')}")


if __name__ == "__main__":
    main()

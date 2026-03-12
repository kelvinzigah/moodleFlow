import requests
from core.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def get_updates(offset: int = 0) -> list:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"offset": offset, "timeout": 5}, timeout=10)
        r.raise_for_status()
        return r.json().get("result", [])
    except requests.exceptions.RequestException as e:
        print(f"Telegram getUpdates failed: {e}")
        return []


def send(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        r.raise_for_status()
        result = r.json()
        if not result.get("ok"):
            print(f"Telegram error: {result.get('description')}")
    except requests.exceptions.RequestException as e:
        print(f"Telegram request failed: {e}")

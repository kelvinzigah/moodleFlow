import re
import requests
from typing import Optional, Tuple
from core.config import MOODLE_TOKEN, MOODLE_URL, MOODLE_USER_ID


def get_messages() -> Tuple[dict, Optional[str]]:
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "core_message_get_messages",
        "moodlewsrestformat": "json",
        "useridto": MOODLE_USER_ID,
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


def strip_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text)

import os
from dotenv import load_dotenv

load_dotenv()

MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_USER_ID = os.getenv("MOODLE_USER_ID")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

SEEN_IDS_FILE = os.path.join(DATA_DIR, "seen_ids.json")
CREDENTIALS_FILE = os.path.join(DATA_DIR, "credentials.json")
TOKEN_FILE = os.path.join(DATA_DIR, "token.json")

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar"]

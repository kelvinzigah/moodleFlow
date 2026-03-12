import os
from dotenv import load_dotenv

load_dotenv()

# Moodle
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_USER_ID = os.getenv("MOODLE_USER_ID")

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Notion
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_CLASSES_DB = "1782534950e880549130df58ee844bf1"
NOTION_ASSIGNMENTS_DB = "1782534950e88038b550daa0c15295a9"
NOTION_TOPICS_DB = "1782534950e8809fb0e9fdb29b2c9a93"
NOTION_STUDY_SESSIONS_DB = "17c2534950e880489958f8d019924e31"

# State
SEEN_IDS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "seen_ids.json")
SEEN_COURSE_IDS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "seen_moodle_course_ids.json")
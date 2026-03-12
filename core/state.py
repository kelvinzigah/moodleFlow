import json
import os
from core.config import SEEN_IDS_FILE, SEEN_COURSE_IDS_FILE

def load_seen_ids():
    if os.path.exists(SEEN_IDS_FILE):
        with open(SEEN_IDS_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen_ids(seen_ids):
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(seen_ids), f)

def load_seen_course_ids() -> dict:
    if os.path.exists(SEEN_COURSE_IDS_FILE):
        with open(SEEN_COURSE_IDS_FILE) as f:
            return json.load(f)
    return {}

def save_seen_course_ids(data: dict):
    with open(SEEN_COURSE_IDS_FILE, "w") as f:
        json.dump(data, f, indent=2)
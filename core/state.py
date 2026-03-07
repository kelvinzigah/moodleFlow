import json
import os
from core.config import SEEN_IDS_FILE


def load_seen_ids() -> set:
    if os.path.exists(SEEN_IDS_FILE):
        with open(SEEN_IDS_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen_ids(seen_ids: set) -> None:
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(seen_ids), f)

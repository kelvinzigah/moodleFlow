import requests
from core.config import (
    NOTION_API_KEY,
    NOTION_CLASSES_DB,
    NOTION_ASSIGNMENTS_DB,
    NOTION_TOPICS_DB,
)

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def find_class_by_moodle_id(moodle_course_id: int):
    """Primary lookup: query Classes DB by Moodle Course ID (number property)."""
    url = f"https://api.notion.com/v1/databases/{NOTION_CLASSES_DB}/query"
    payload = {
        "filter": {
            "property": "Moodle Course ID",
            "number": {"equals": moodle_course_id}
        }
    }
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        return results[0]["id"] if results else None
    except Exception as e:
        print(f"Notion class lookup by moodle_id failed: {e}")
        return None


def find_class_by_course_code(course_code: str):
    """Fallback lookup by Course Code title field (used when moodle_course_id is unavailable)."""
    url = f"https://api.notion.com/v1/databases/{NOTION_CLASSES_DB}/query"
    payload = {
        "filter": {
            "property": "Course Code",
            "title": {"contains": course_code}
        }
    }
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        return results[0]["id"] if results else None
    except Exception as e:
        print(f"Notion class lookup by course_code failed: {e}")
        return None


def create_class(course_code: str, name: str, moodle_course_id: int = None,
                 professor: str = None, credits: int = None,
                 office_hours: str = None, textbooks: str = None):
    """Create a new entry in the Classes database."""
    url = "https://api.notion.com/v1/pages"
    properties = {
        "Course Code": {"title": [{"text": {"content": course_code}}]},
        "Name":        {"rich_text": [{"text": {"content": name}}]},
        "Active": {"checkbox": True},
    }
    if moodle_course_id is not None:
        properties["Moodle Course ID"] = {"number": moodle_course_id}
    if professor:
        properties["Professor"] = {"rich_text": [{"text": {"content": professor}}]}
    if credits is not None:
        properties["Credits"] = {"number": credits}
    if office_hours:
        properties["Office Hours"] = {"rich_text": [{"text": {"content": office_hours}}]}
    if textbooks:
        properties["TextBooks"] = {"rich_text": [{"text": {"content": textbooks}}]}
    payload = {"parent": {"database_id": NOTION_CLASSES_DB}, "properties": properties}
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        print(f"Notion class created: {course_code} — {name}")
        return r.json().get("url", "")
    except Exception as e:
        print(f"Notion class creation failed: {e}")
        return None


def find_topic_by_name(name: str, class_page_id: str):
    """Dedup check: find a topic by name within a given class."""
    url = f"https://api.notion.com/v1/databases/{NOTION_TOPICS_DB}/query"
    payload = {
        "filter": {
            "property": "Name",
            "title": {"equals": name}
        }
    }
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        return results[0]["id"] if results else None
    except Exception as e:
        print(f"Notion topic lookup failed: {e}")
        return None


def create_topic(name: str, class_page_id: str, week_taught=None,
                 exam_relevance: str = None, textbook_section: str = None):
    """Create a new entry in the Topics database."""
    url = "https://api.notion.com/v1/pages"
    properties = {
        "Name": {"title": [{"text": {"content": name}}]},
        "📎 Classes ": {"relation": [{"id": class_page_id}]},
    }
    if exam_relevance:
        properties["Exam Relevance"] = {"select": {"name": exam_relevance}}
    if week_taught:
        properties["Week Taught"] = {"multi_select": [{"name": w} for w in week_taught]}
    if textbook_section:
        properties["Textbook Section"] = {"rich_text": [{"text": {"content": textbook_section}}]}
    payload = {"parent": {"database_id": NOTION_TOPICS_DB}, "properties": properties}
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        page = r.json()
        print(f"Notion topic created: {name}")
        return page["id"]
    except Exception as e:
        print(f"Notion topic creation failed: {e}")
        return None


def find_assignment_by_name(name: str, class_page_id: str):
    """Dedup check: find an assignment by name within a given class."""
    url = f"https://api.notion.com/v1/databases/{NOTION_ASSIGNMENTS_DB}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Name", "title": {"equals": name}},
                {"property": "🏛️ Classes ", "relation": {"contains": class_page_id}}
            ]
        }
    }
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        return results[0]["id"] if results else None
    except Exception as e:
        print(f"Notion assignment lookup failed: {e}")
        return None


def create_assignment(parsed, subject, class_page_id=None, status="To Do"):
    """Create a new entry in the Assignments database."""
    url = "https://api.notion.com/v1/pages"

    urgency = parsed.get("urgency", 1)
    if urgency >= 5:
        impact = "Important"
    elif urgency == 4:
        impact = "High"
    elif urgency == 3:
        impact = "Medium"
    else:
        impact = "Low"

    properties = {
        "Name": {
            "title": [{"text": {"content": subject}}]
        },
        "Status": {
            "select": {"name": status}
        },
        "Type": {
            "select": {"name": parsed.get("task_type", "other").capitalize()}
        },
        "Impact": {
            "select": {"name": impact}
        },
    }

    # Add due date if present
    if parsed.get("due_date"):
        due = parsed["due_date"]
        if parsed.get("due_time"):
            due = f"{due}T{parsed['due_time']}:00+00:00"
        properties["Due Date"] = {"date": {"start": due}}

    # Add estimated hours by task type
    hours_map = {"lab": 4, "exam": 7, "homework": 1, "quiz": 1, "project": 12, "assignment": 1}
    hours = hours_map.get(parsed.get("task_type", "").lower())
    if hours:
        properties["Estimated Hours"] = {"number": hours}

    # Add suggested topics (staging field only)
    topics = parsed.get("suggested_topics")
    if topics:
        properties["Suggested Topics"] = {
            "rich_text": [{"text": {"content": topics}}]
        }

    # Link to class
    if class_page_id:
        properties["🏛️ Classes "] = {
            "relation": [{"id": class_page_id}]
        }

    payload = {
        "parent": {"database_id": NOTION_ASSIGNMENTS_DB},
        "properties": properties,
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": parsed.get("summary", "")}}]
                }
            }
        ]
    }

    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        page = r.json()
        page_url = page.get("url", "")
        print(f"Notion assignment created: {subject}")
        return page_url
    except Exception as e:
        print(f"Notion assignment creation failed: {e}")
        return None

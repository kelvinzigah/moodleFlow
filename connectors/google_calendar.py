from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from core.config import CREDENTIALS_FILE, TOKEN_FILE, GOOGLE_SCOPES


def get_service():
    creds = None
    if __import__("os").path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GOOGLE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def create_event(service, parsed: dict, subject: str) -> Optional[str]:
    if not parsed.get("has_deadline") or not parsed.get("due_date"):
        return None

    due_date = parsed["due_date"]
    due_time = parsed.get("due_time") or "23:59"
    start_dt = f"{due_date}T{due_time}:00"

    task_type = parsed.get("task_type", "task").capitalize()
    course = parsed.get("course_code") or ""
    title = f"[{course}] {task_type}: {subject}" if course else f"{task_type}: {subject}"

    event = {
        "summary": title,
        "description": parsed.get("summary", ""),
        "start": {"dateTime": start_dt, "timeZone": "America/Toronto"},
        "end": {"dateTime": start_dt, "timeZone": "America/Toronto"},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 1440},
                {"method": "popup", "minutes": 120},
            ],
        },
        "colorId": "11" if parsed.get("urgency", 1) >= 4 else "9",
    }

    try:
        created = service.events().insert(calendarId="primary", body=event).execute()
        print(f"Calendar event created: {title}")
        return created.get("htmlLink")
    except Exception as e:
        print(f"Calendar event creation failed: {e}")
        return None

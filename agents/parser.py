import re
import json
import time
from typing import Optional
import anthropic
from core.config import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def parse_message(subject: str, body: str) -> Optional[dict]:
    prompt = f"""You are a university student assistant.
    Your job is to recieve the moodle messages I send you, analyse them in context,
    return to me the a json in the format below:

Subject: {subject}
Body: {body}

Return ONLY a JSON object with these fields, nothing else:
{{
  "has_deadline": true or false,
  "due_date": "YYYY-MM-DD or null",
  "due_time": "HH:MM or null",
  "task_type": "assignment, lab, exam, quiz, announcement, or other",
  "course_code": "e.g. ENGR 233 or null",
  "action_required": true or false,
  "urgency": 1 to 5,
  "summary": "one line human readable summary"
}}"""

    for attempt in range(3):
        try:
            message = _client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            if not raw:
                raise ValueError("Empty response from AI")
            if raw.startswith("```"):
                raw = re.sub(r'^```(?:json)?\n?', '', raw)
                raw = re.sub(r'\n?```$', '', raw).strip()
            return json.loads(raw)
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 2:
                print(f"API overloaded, retrying in 10s... (attempt {attempt + 1})")
                time.sleep(10)
            else:
                raise

import base64
import json
import re

import anthropic
from core.config import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

EXTRACTION_PROMPT = """You are extracting structured data from a university course outline (syllabus) PDF.

Return ONLY a valid JSON object with exactly these three keys: "class", "topics", "assignments".

Schema:
{
  "class": {
    "course_code": "string (e.g. ELEC 273)",
    "name": "string (full course name)",
    "professor": "string or null",
    "credits": number or null,
    "office_hours": "string or null",
    "textbooks": "string or null (comma-separated if multiple)"
  },
  "topics": [
    {
      "name": "string (concept name)",
      "week_taught": ["1", "2"] or null,  // list of strings from ["0","1",...,"12","n/a"]
      "exam_relevance": "Low" or "Medium" or "High" or "Critical" or null,
      "textbook_section": "string or null"
    }
  ],
  "assignments": [
    {
      "name": "string (descriptive name)",
      "type": "lab" or "exam" or "homework" or "quiz" or "project" or "assignment" or "other",
      "due_date": "YYYY-MM-DD" or null,
      "suggested_topics": "comma-separated topic names or null"
    }
  ]
}

Rules:
- Extract ALL topics/concepts listed in the course schedule or content sections.
- Extract ALL assessments: labs, exams, quizzes, projects, homework sets, assignments.
- Use null for any field that cannot be confidently inferred from the document.
- week_taught must only contain strings from the set: "0" through "12" and "n/a".
- exam_relevance: infer from weighting, emphasis, or explicit labels. Null if unclear.
- due_date: use YYYY-MM-DD format. Null if no specific date is given.
- All assignment Status values will be set to "Tentative" by the system — do not include Status in your output.
- Do not add any commentary, markdown, or text outside the JSON object.
"""


def parse_outline(pdf_path: str) -> dict:
    """Extract class, topics, and assignments from a course outline PDF."""
    with open(pdf_path, "rb") as f:
        pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

    message = _client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data,
                    }
                },
                {"type": "text", "text": EXTRACTION_PROMPT}
            ]
        }]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r'^```(?:json)?\n?', '', raw)
        raw = re.sub(r'\n?```$', '', raw).strip()
    return json.loads(raw)

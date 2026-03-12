# Notion Learning OS — Claude Code Context

## Project Overview

This is a personal Learning OS for a student at Concordia University (Electrical Engineering).
The pipeline moves data from **Moodle → AI parsing → Notion databases → Telegram notifications**.
Google Calendar integration has been removed. All due date and scheduling logic is handled through
Notion natively. Telegram output remains active.

Pipeline architecture reference: `notion-pipeline.html` in the project root.

---

## Active Build Phases

| Phase | What it does | Status |
|-------|-------------|--------|
| Phase 3 | Moodle message → auto-create Assignments in Notion | Active |
| Phase 4 | Course outline PDF → bulk-populate Topics DB | Active |
| Phase 5 | Topic → Assignment relation mapping (confirmed by user) | Active |
| Phase 6 | Spaced repetition engine | Future |

Phase 2 (Google Calendar / standalone AI integration) has been **removed**.
Calendar sync is now handled via Notion's native calendar view or a Notion-side sync only.

---

## Notion Database Schemas

### 1. Classes
> Primary lookup key: `Moodle Course ID` (number). Never look up or create a class by name alone.

| Property | Type | Notes |
|----------|------|-------|
| Course Code | title | e.g. ELEC 273 — **used for text fallback lookup** |
| Name | text | e.g. Fundamentals of Electric Circuits |
| Moodle Course ID | number | **Primary key** |
| Active | checkbox | Set true on creation |
| Professor | text | |
| Office Hours | text | |
| TextBooks | text | |
| Grade Target | select | A, B+, B, C+, C |
| Current Grade | number % | User-entered. Never overwrite. |
| Credits | number | |
| Syllabus URL | url | |
| Topics | relation → Topics | |
| Assignments | relation → Assignments | |

---

### 2. Assignments
> Core fields: `Name` (title) + `🏛️ Classes` relation.

| Property | Type | Notes |
|----------|------|-------|
| Name | title | |
| Status | select | To Do, In Progress, Submitted, Graded, **Tentative** |
| Type | select | Homework, Lab, Exam, Project, Quiz, Assignment, Other, Announcement |
| Due Date | date | Source of truth for all scheduling |
| Date Assigned | date | |
| Estimated Hours | number | See estimation rules below |
| Actual Hours | number | User-entered. **Never overwrite.** |
| Grade Received | number % | User-entered. **Never overwrite.** |
| Submission Link | url | |
| Suggested Topics | text | Comma-separated staging field only. NOT the real relation. |
| Review Needed | checkbox | |
| Blocked By | self-relation → Assignments | |
| 🏛️ Classes | relation → Classes | |
| Related Materials (Topics) | relation → Topics | Human-confirmed only (Workflow C) |
| Impact | select | Low, Medium, High, Important |

**Estimated Hours by type:**
- Lab → 3–6 hrs
- Exam → 5–10 hrs
- Homework / Quiz → 1–2 hrs
- Project → 8–20 hrs

---

### 3. Topics
> One page per concept per course.

| Property | Type | Notes |
|----------|------|-------|
| Name | title | |
| 📎 Classes | relation → Classes | |
| Assignments | relation → Assignments | |
| Study Sessions | relation → Study Sessions | |
| Understanding | select | Almost No Understanding, Some Understanding, Moderate Understanding, Good Understanding, Great Understanding, No Misunderstandings |
| Mastery Level | select | Struggling, Developing, Proficient, Mastered |
| Exam Relevance | select | Low, Medium, High, Critical |
| Week Taught | multi-select | 0–12, n/a |
| Textbook Section | text | |
| Last Reviewed | date | Updated when study session is logged |
| Times Reviewed | number | Incremented when study session is logged |
| Next Review | date | Updated when study session is logged |
| Duration | date range | |
| done | checkbox | |

---

### 4. Study Sessions
> One per session, linked to a single topic (relation limit: 1).

| Property | Type | Notes |
|----------|------|-------|
| Name | title | |
| Topics | relation → Topics | Limit 1 |
| Understanding | select | Same scale as Topics |
| Reviewed On | date | |
| done | checkbox | |
| Next Review | formula | Almost No / Some → same day · Moderate → +1d · Good → +2d · Great → +4d · No Misunderstandings → +7d |

When a completed study session is logged, update these fields on the linked Topic page:
`Last Reviewed`, `Times Reviewed` (increment), `Next Review`.

---

## Core Workflows

### Workflow A — Moodle Message → Assignment (Phase 3)
1. Parse the raw Moodle notification message.
2. Extract `Moodle Course ID` from the message's `customdata.courseid` field. Fall back to AI-parsed `course_code` text if unavailable.
3. If the `Moodle Course ID` has never been seen → send a Telegram alert with `/addcourse` and `/ignorecourse` instructions. **Never auto-create a class from a message.** Wait for user action.
4. If course status is `"ignored"` → skip all further processing for that message.
5. Look up the class in Classes DB by `Moodle Course ID` (primary). Fall back to `Course Code` text search if ID is unavailable.
6. If class not found → send Telegram "class not found" alert. Do not create assignment.
7. Create a new Assignments page. Set `Status = "To Do"`. Link via `🏛️ Classes`.
8. Write inferred topic names as comma-separated text into `Suggested Topics` only.
9. Set `Estimated Hours` based on type rules above.

### Workflow B — Course Outline PDF → Bulk Population (Phase 4)
1. Parse the course outline PDF or extracted text.
2. If the course doesn't exist in Classes → create it.
3. Extract all topics → one Topics page each. Set `📎 Classes`, `Week Taught`, `Textbook Section`, `Exam Relevance` where inferable.
4. Extract all assessments → one Assignments page each. Set `Status = "Tentative"`, `Type`, `Due Date`, `🏛️ Classes`, `Estimated Hours`.
5. No duplicates. If a topic or assignment with the same name already exists for that course → update, don't create.

### Workflow C — Topic → Assignment Mapping (Phase 5)
1. After any assignment is created, review its `Suggested Topics` staging field.
2. Present the suggested topic names to the user and request confirmation.
3. On confirmation only: set `Related Materials (Topics)` on the Assignment, and set the inverse `Assignments` relation on each linked Topic page.
4. Never write to `Related Materials (Topics)` without explicit user confirmation.

---

## Uncertainty Handling

When a field value cannot be confidently extracted or inferred:
- Leave the field **blank**. Do not guess silently.
- List all uncertain fields at the end of the response, e.g.:
  > "I left `Due Date` and `Type` blank — can you confirm these so I can update the entry?"
- Wait for user confirmation before updating.
- On confirmation, update **only** the flagged fields. Do not touch anything already written.

---

## Course Detection

When the pipeline sees a `Moodle Course ID` for the first time, it:
1. Stores it in `data/seen_moodle_course_ids.json` with `status: "pending"`
2. Sends a Telegram alert with the detected course code and command instructions

**State file:** `data/seen_moodle_course_ids.json`
```json
{
  "12345": {"course_code": "ELEC 273", "status": "pending"},
  "67890": {"course_code": "unknown",  "status": "ignored"}
}
```
Status values: `"pending"` (awaiting user decision), `"ignored"` (skip all messages), `"active"` (class created).

**Telegram commands:**
- Add a class: `/addcourse MOODLE_ID | COURSE_CODE | Course Name | Professor | Credits`
  - Example: `/addcourse 12345 | ELEC 273 | Fundamentals of Electric Circuits | Dr. Emami | 3`
- Ignore a course: `/ignorecourse MOODLE_ID`

---

## Hard Rules

- `Moodle Course ID` is always the primary key. Never use course name as a lookup key if an ID is available.
- **Never auto-create a Classes entry from a Moodle message.** Classes are created only via `/addcourse` command or during Workflow B (user-provided course outline).
- `Suggested Topics` is a staging field only. `Related Materials (Topics)` is set by human confirmation exclusively.
- `Status = "Tentative"` for anything sourced from a course outline before official Moodle posting.
- Never overwrite: `Actual Hours`, `Grade Received`, `Current Grade`.
- Google Calendar API is removed. Due dates live in Notion. Do not reintroduce any gcal API calls.
- Telegram notification output is active and should be preserved.
- For pipeline logic, trigger sequence, or output routing questions → refer to `notion-pipeline.html`.

---

## Notion MCP Server

A Notion MCP server is available in this project. Use it for **all direct Notion interactions** — reading live data, verifying schemas, inspecting pages — rather than making raw API calls in scripts or relying on memory alone.

### Available MCP Tools

| Tool | Purpose |
|------|---------|
| `API-retrieve-a-database` | Get live schema (property names, types, options) for any DB |
| `API-query-data-source` | Query/filter database rows |
| `API-post-search` | Search pages/databases by title or content |
| `API-retrieve-a-page` | Read a specific page and its properties |
| `API-retrieve-a-page-property` | Read a single property value from a page |
| `API-post-page` | Create a new page (in a database or as a child) |
| `API-patch-page` | Update properties on an existing page |
| `API-move-page` | Move a page to a different parent |
| `API-get-block-children` | Read the block content of a page |
| `API-patch-block-children` | Append or update blocks inside a page |
| `API-update-a-block` / `API-delete-a-block` | Edit or remove a specific block |
| `API-retrieve-a-block` | Get a single block |
| `API-create-a-comment` / `API-retrieve-a-comment` | Comments on pages |
| `API-get-self` / `API-get-user` / `API-get-users` | Notion workspace user info |

### Database IDs (from `core/config.py`)

| Database | ID |
|----------|----|
| Classes | `1782534950e880549130df58ee844bf1` |
| Assignments | `1782534950e88038b550daa0c15295a9` |
| Topics | `1782534950e8809fb0e9fdb29b2c9a93` |
| Study Sessions | `17c2534950e880489958f8d019924e31` |

---

## Notion Script Validation Protocol

**Before modifying any script that reads from or writes to Notion**, use the MCP server to verify the live schema matches what the script expects. This prevents silent field mismatches.

### Steps

1. **Retrieve the live schema** using `API-retrieve-a-database` for the relevant database ID.
2. **Cross-check every property** the script touches against the live schema:
   - Property name (exact string, including emoji prefix)
   - Property type (`title`, `rich_text`, `number`, `select`, `multi_select`, `date`, `checkbox`, `url`, `relation`)
   - Select/multi-select option values (exact casing)
3. **Fix any mismatch** in the script before proceeding. Common drift points:
   - Emoji prefixes on relation fields (`🏛️ Classes`, `📎 Classes`)
   - Select option casing (e.g. `"To Do"` vs `"to do"`)
   - Date format — always ISO 8601 (`YYYY-MM-DD`); time as `HH:MM:SS` if needed
   - `rich_text` vs `text` — Notion API always uses `rich_text` in payloads
4. **Confirm the write result** using `API-retrieve-a-page` after any create or update to verify the values landed correctly.

### Known Property Name Reference (verified against `connectors/notion.py`)

**Classes DB write fields:**
```
"Course Code"       → title
"Name"              → rich_text
"Moodle Course ID"  → number
"Active"            → checkbox
"Professor"         → rich_text
"Office Hours"      → rich_text
"TextBooks"         → rich_text
"Credits"           → number
"Syllabus URL"      → url
```

**Assignments DB write fields:**
```
"Name"                     → title
"Status"                   → select   (To Do | In Progress | Submitted | Graded | Tentative)
"Type"                     → select   (Homework | Lab | Exam | Project | Quiz | Assignment | Other | Announcement)
"Due Date"                 → date
"Date Assigned"            → date
"Estimated Hours"          → number
"Suggested Topics"         → rich_text  ← staging only, never the real relation
"🏛️ Classes"              → relation
"Related Materials (Topics)" → relation  ← human-confirmed only (Workflow C)
"Impact"                   → select   (Low | Medium | High | Important)
"Review Needed"            → checkbox
```

**Topics DB write fields:**
```
"Name"             → title
"📎 Classes "      → relation  ← trailing space in actual Notion property name
"Exam Relevance"   → select   (Low | Medium | High | Critical)
"Week Taught"      → multi_select  (options: "0"–"12", "n/a")
"Textbook Section" → rich_text
"Understanding"    → select   (Almost No Understanding | Some Understanding | Moderate Understanding | Good Understanding | Great Understanding | No Misunderstandings)
"Mastery Level"    → select   (Struggling | Developing | Proficient | Mastered)
"Last Reviewed"    → date
"Times Reviewed"   → number
"Next Review"      → date
"done"             → checkbox
```

**Study Sessions DB write fields:**
```
"Name"          → title
"Topics"        → relation  (limit 1)
"Understanding" → select   (same scale as Topics)
"Reviewed On"   → date
"done"          → checkbox
```

### Urgency → Impact Mapping (parser.py → Notion)

| Urgency (AI output) | Impact (Notion select) |
|---------------------|----------------------|
| 5 | Important |
| 4 | High |
| 3 | Medium |
| 1–2 | Low |

### Estimated Hours defaults (by type)

| Type | Default value written |
|------|-----------------------|
| lab | 4 |
| exam | 7 |
| homework | 1 |
| quiz | 1 |
| project | 12 |
| assignment | 1 |
| other / announcement | 0 or omitted |

---

## CLAUDE.md Update Protocol

When the user shares a relevant update (new schema field, changed workflow, new phase, removed
integration, etc.), suggest whether it should be added to this file with the prompt:

> "This sounds like a CLAUDE.md update — want me to add it?"

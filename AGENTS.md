# School Assistant — Codex Context

## Project Overview

School Assistant is an always-on student service evolving from the existing `moodleFlow` codebase.
It continuously polls Moodle, keeps a dedicated Google Calendar synchronized, downloads course
materials to Google Drive, and sends meaningful changes through Telegram. Notion remains available
as an optional destination connector; it is not the architectural foundation.

Canonical identity:
- **Product name:** School Assistant
- **GitHub repository and historical codebase:** `moodleFlow` (keep this name)
- **Development strategy:** evolve this repository in place and preserve its Git history

Current architecture sources of truth:
- Implementation-ready PRD and latest decisions: `https://github.com/kelvinzigah/moodleFlow/issues/1`
- Visual architecture: `C:\Users\KZIGAH\.lavish\school-assistant-architecture.html`
- Technical specification: `C:\Users\KZIGAH\Documents\synced-vault\projects\moodleFlow\docs\spec\school-assistant-spec.md`
- Resolved project language: `CONTEXT.md`
- Accepted architectural decisions: `docs/adr/`

When older visual/spec details conflict with GitHub issue #1 or an accepted ADR, use the issue and
ADR. In particular, the original VPS-only startup assumption has been replaced by the portable
local-first backend plan below.

---

## Target Architecture

- **Frontend:** React dashboard and onboarding app hosted on Vercel. Use a temporary `vercel.app`
  hostname until the user buys a custom domain, then attach that domain to the Vercel project.
- **Backend host:** FastAPI, the APScheduler worker, PostgreSQL, and Telegram integration initially
  run on the user's current local machine. The final target is a small VPS, with another always-on
  laptop also supported as an intermediate host.
- **Portability:** package the backend as the same Docker Compose stack on every host. Keep durable
  state in PostgreSQL and keep secrets, API base URLs, OAuth redirects, CORS origins, Telegram mode,
  and host-specific settings in environment configuration. Do not bake Windows paths, hostnames,
  or machine identity into application logic.
- **Reachability:** a Vercel deployment cannot call a backend available only at `localhost`. During
  local development, run the frontend locally or expose FastAPI through a temporary HTTPS tunnel.
  Before production OAuth launches, use a stable HTTPS API hostname; later point the purchased
  custom domain at Vercel and its `api` subdomain at the backend host.
- **Execution boundary:** the web app handles onboarding, configuration, OAuth, and status only.
  It never performs Moodle polling or synchronization work.
- **Coordination:** the API and worker communicate through PostgreSQL, not by calling each other.
- **Core sync model:** take a current Moodle snapshot, compare it with the stored ledger, derive a
  pure `SyncPlan`, execute creates/updates/deletes, then update the ledger and notify through Telegram.
- **Calendar:** one-way Moodle → dedicated Google Calendar named `School`, every 15 minutes.
- **Files:** Moodle → Google Drive using the least-privilege `drive.file` scope, every 30 minutes.
- **Messages:** poll and classify Moodle messages every 20 minutes; notify Telegram and optionally
  write to Notion when the Notion feature flag is enabled.
- **AI boundary:** use the direct Anthropic SDK with typed validation for bounded classification and
  extraction. Do not use LangChain or LangGraph in the deterministic MVP core. A future isolated,
  genuinely stateful multi-step agent may adopt LangGraph without owning sync or ledger state.
- **Multi-user seam:** remain owner-first, but key credentials, configuration, ledgers, and jobs by
  `user_id` so adding users later does not require a rewrite.

## Active Build Phases

| Phase | What it does | Status |
|-------|-------------|--------|
| Phase 0 | Monorepo foundation, shared core, PostgreSQL schema, Docker | Next |
| Phase 1 | Portable message loop and Telegram bot running on the current local machine | Planned |
| Phase 2 | Google Calendar ledger + diff synchronization | Planned |
| Phase 3 | Google Drive course-file synchronization | Planned |
| Phase 4 | Vercel-hosted onboarding, settings, and status dashboard | Planned |
| Phase 5 | Hardening, backups, crash drills, and first additional user | Future |

The existing Notion Workflows A–C remain valid optional connector behavior during the transition.
They do not define the new product's build-phase numbering.

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
| Due Date | date | Notion-side due date when the connector is enabled; Google Calendar sync derives from Moodle |
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

## Optional Notion Workflows

These workflows are preserved behind the per-user Notion feature flag. Calendar, Drive, and
Telegram must remain functional when Notion is disabled.

### Workflow A — Moodle Message → Assignment
1. Parse the raw Moodle notification message.
2. Extract `Moodle Course ID` from the message's `customdata.courseid` field. Fall back to AI-parsed `course_code` text if unavailable.
3. If the `Moodle Course ID` has never been seen → send a Telegram alert with `/addcourse` and `/ignorecourse` instructions. **Never auto-create a class from a message.** Wait for user action.
4. If course status is `"ignored"` → skip all further processing for that message.
5. Look up the class in Classes DB by `Moodle Course ID` (primary). Fall back to `Course Code` text search if ID is unavailable.
6. If class not found → send Telegram "class not found" alert. Do not create assignment.
7. Create a new Assignments page. Set `Status = "To Do"`. Link via `🏛️ Classes`.
8. Write inferred topic names as comma-separated text into `Suggested Topics` only.
9. Set `Estimated Hours` based on type rules above.

### Workflow B — Course Outline PDF → Bulk Population
1. Parse the course outline PDF or extracted text.
2. If the course doesn't exist in Classes → create it.
3. Extract all topics → one Topics page each. Set `📎 Classes`, `Week Taught`, `Textbook Section`, `Exam Relevance` where inferable.
4. Extract all assessments → one Assignments page each. Set `Status = "Tentative"`, `Type`, `Due Date`, `🏛️ Classes`, `Estimated Hours`.
5. No duplicates. If a topic or assignment with the same name already exists for that course → update, don't create.

### Workflow C — Topic → Assignment Mapping
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

In the current legacy implementation, when the pipeline sees a `Moodle Course ID` for the first time, it:
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

During Phase 1, preserve these statuses and behaviors while moving the state into PostgreSQL keyed
by `user_id`. Retire the JSON state file only after the database-backed path is verified.

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
- Google Calendar is a primary integration. Sync one-way from Moodle into the dedicated `School`
  calendar through the ledger + diff engine; do not add two-way calendar sync.
- Google Drive is a primary integration for course materials. Preserve file identity and upload
  changed content as a revision rather than creating duplicate filenames.
- Notion must remain optional and controlled by a feature flag. Calendar, Drive, and Telegram flows
  cannot depend on Notion being configured or available.
- The Vercel frontend never runs polling or sync jobs. All persistent work belongs on the portable
  backend worker, regardless of whether its current host is this machine, another laptop, or a VPS.
- Scheduler timing must not be the source of truth. On startup or after downtime, jobs reconcile
  Moodle against PostgreSQL so sleep, reboot, or host migration cannot lose or duplicate work.
- LLM output may classify or extract data, but it never decides or directly executes Calendar/Drive
  creates, updates, or deletes. The pure ledger + diff engine owns those decisions.
- Telegram notification output is active and should be preserved.
- For system architecture, trigger sequences, or output routing, use
  `C:\Users\KZIGAH\.lavish\school-assistant-architecture.html` and the technical specification listed above.

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

## AGENTS.md Update Protocol

When the user shares a relevant update (new schema field, changed workflow, new phase, removed
integration, etc.), suggest whether it should be added to this file with the prompt:

> "This sounds like a AGENTS.md update — want me to add it?"

---

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the five canonical triage labels defined in `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository using root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.

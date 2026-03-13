# moodleFlow

test

A personal Learning OS pipeline for Concordia University (Electrical Engineering).
Automatically moves data from **Moodle → AI parsing → Notion databases → Telegram notifications**.

---

## How It Works

### The Pipeline

```
Moodle (new messages)
    ↓
main.py (polls every 20 min)
    ↓
Claude AI (agents/parser.py)     ← classifies message, extracts due date, type, topics
    ↓
Notion (connectors/notion.py)    ← creates Assignment page, links to Class
    ↓
Telegram (connectors/telegram.py) ← sends confirmation to your phone
```

### Workflows

**Workflow A — Live Moodle messages → Assignments (runs automatically)**
1. `main.py` polls Moodle every 20 minutes for new messages.
2. Each message is sent raw to Telegram so you always see it.
3. Claude AI parses the message to decide: is this an assignment? What type? When is it due?
4. The pipeline looks up the course in your Notion **Classes** database using the Moodle Course ID.
   - If the course has never been seen before, a Telegram alert is sent asking you to add or ignore it (see Telegram commands below). Nothing is created until you respond.
   - If the course is marked "ignored", the message is skipped entirely.
5. A new page is created in the Notion **Assignments** database, linked to the Class, with status `To Do`.

**Workflow B — Course outline PDF → Bulk population (run manually)**
1. You run `process_outline.py` with a path to a course outline PDF.
2. Claude AI reads the PDF and extracts the class info, all topics, and all assessments.
3. The Class is created in Notion if it doesn't exist yet.
4. All topics are created in the **Topics** database, each linked to the Class.
5. All assessments are created in the **Assignments** database with status `Tentative`.
6. A Telegram summary is sent with counts of what was created.

**Workflow C — Topic → Assignment mapping (manual confirmation)**
- After assignments are created, `Suggested Topics` is a staging text field holding inferred topic names.
- You review and confirm which topics relate to which assignment — only then is the real `Related Materials` relation written in Notion.

### Notion Databases

| Database | Purpose |
|----------|---------|
| **Classes** | One page per course. Primary key: Moodle Course ID. |
| **Assignments** | One page per task/assessment. Linked to a Class. |
| **Topics** | One concept per page. Linked to a Class. |
| **Study Sessions** | One session per page. Linked to a Topic. |

### Telegram Commands

Send these to your bot to manage course detection:

```
/addcourse MOODLE_ID | COURSE_CODE | Course Name | Professor | Credits
/ignorecourse MOODLE_ID
```

Example:
```
/addcourse 12345 | ELEC 342 | Discrete-Time Signals and Systems | Dr. Smith | 3
```

### Key Files

```
main.py                  ← main loop (Workflow A)
process_outline.py       ← PDF bulk importer (Workflow B)
agents/parser.py         ← Claude AI message parser
agents/outline_parser.py ← Claude AI PDF extractor
connectors/notion.py     ← all Notion API calls
connectors/moodle.py     ← Moodle REST API
connectors/telegram.py   ← Telegram bot
core/config.py           ← loads all env vars
core/state.py            ← tracks seen message IDs and course IDs
data/                    ← JSON state files (gitignored)
```

---

## Setup (for anyone on Windows, Mac, or Linux)

### Prerequisites

You need accounts and API keys for:
- **Moodle** — your institution's Moodle instance (needs a web service token)
- **Telegram** — a bot created via [@BotFather](https://t.me/BotFather), and your chat ID
- **Anthropic** — an API key from [console.anthropic.com](https://console.anthropic.com)
- **Notion** — an integration token from [notion.so/my-integrations](https://www.notion.so/my-integrations), plus four databases (Classes, Assignments, Topics, Study Sessions) shared with the integration

### 1. Clone the repo

```bash
git clone <repo-url>
cd moodleFlow
```

### 2. Create a virtual environment

**Linux / Mac:**
```bash
python3 -m venv venv
```

**Windows:**
```powershell
python -m venv venv
```

### 3. Install dependencies

**Linux / Mac:**
```bash
venv/bin/python -m pip install -r requirements.txt
```

**Windows:**
```powershell
venv\Scripts\python -m pip install -r requirements.txt
```

> Always use `python -m pip` (not `pip` directly) to ensure packages install into the venv.

### 4. Create your `.env` file

Copy the template and fill in your values:

```bash
cp .env.example .env
```

`.env` contents:

```env
MOODLE_TOKEN=your_moodle_web_service_token
MOODLE_URL=https://moodle.yourcampus.ca
MOODLE_USER_ID=your_moodle_numeric_user_id

TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

ANTHROPIC_API_KEY=your_anthropic_api_key

NOTION_API_KEY=your_notion_integration_secret
NOTION_CLASSES_DB=your_classes_database_id
NOTION_ASSIGNMENTS_DB=your_assignments_database_id
NOTION_TOPICS_DB=your_topics_database_id
NOTION_STUDY_SESSIONS_DB=your_study_sessions_database_id
```

### 5. Set up Notion databases

Create four databases in Notion with these schemas (see CLAUDE.md for full property lists):

- **Classes** — title: `Course Code`, number: `Moodle Course ID`, checkbox: `Active`, text fields for Professor, Credits, etc.
- **Assignments** — title: `Name`, select: `Status`, select: `Type`, date: `Due Date`, relation: `🏛️ Classes `, etc.
- **Topics** — title: `Name`, relation: `📎 Classes `, multi-select: `Week Taught`, select: `Exam Relevance`, etc.
- **Study Sessions** — title: `Name`, relation: `Topics`, select: `Understanding`, date: `Reviewed On`

Share each database with your Notion integration (click "..." → "Connect to" → your integration name).

Copy each database ID from its URL:
```
https://notion.so/yourworkspace/DATABASE_ID_HERE?v=...
```

### 6. Run

**Start the live pipeline (Workflow A):**

Linux / Mac:
```bash
venv/bin/python main.py
```

Windows:
```powershell
venv\Scripts\python main.py
```

**Import a course outline PDF (Workflow B):**

Linux / Mac:
```bash
venv/bin/python process_outline.py /path/to/outline.pdf
```

Windows:
```powershell
venv\Scripts\python process_outline.py C:\path\to\outline.pdf
```

---

## Installing a new package

**Linux / Mac:**
```bash
venv/bin/python -m pip install <package-name>
venv/bin/python -m pip freeze > requirements.txt
```

**Windows:**
```powershell
venv\Scripts\python -m pip install <package-name>
venv\Scripts\python -m pip freeze > requirements.txt
```

---

## Notes

- The `data/` folder holds JSON state files that track which Moodle messages and course IDs have been seen. These are gitignored and will be created automatically on first run.
- Never auto-create a Class from a Moodle message — always use `/addcourse` or Workflow B.
- `Suggested Topics` on Assignments is a staging field only. The real `Related Materials (Topics)` relation requires manual confirmation (Workflow C).

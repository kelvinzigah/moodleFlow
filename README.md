# School Assistant

School Assistant is the next version of `moodleFlow`: a portable, worker-driven backend that
turns Moodle activity into a durable academic ledger and keeps downstream tools synchronized.
The GitHub repository remains named `moodleFlow`.

The deployment split is intentional:

- Vercel hosts the future frontend and dashboard.
- This Compose stack hosts PostgreSQL, migrations, the FastAPI service, and the worker.
- The same stack can run on this Windows machine now and move later to an always-on laptop or VPS.
- Notion is an optional destination, not the system of record.

## Phase 0 foundation

The current foundation includes:

- shared typed settings, SQLAlchemy models, credential encryption, and legacy adapters;
- a FastAPI health endpoint at `GET /health`;
- an APScheduler worker with a durable `job_runs` heartbeat;
- PostgreSQL schema managed by Alembic;
- an idempotent importer for the legacy JSON state files;
- Docker Compose and CI verification.

## Run locally with Docker

1. Copy `.env.example` to `.env`.
2. Generate a Fernet key and assign it to `CREDENTIAL_KEY`:

   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. Change `POSTGRES_PASSWORD`, then start the backend:

   ```powershell
   docker compose up -d --build
   ```

4. Verify the API:

   ```powershell
   Invoke-RestMethod http://localhost:8000/health
   ```

The database is stored in the `postgres_data` named volume. Moving hosts means copying `.env`
and the database backup, then running the same Compose file on the new machine.

## Owner and legacy-state migration

After the stack is running, create the initial owner and import the existing JSON state:

```powershell
docker compose run --rm api school-assistant create-owner `
  --email you@example.com --display-name "Your Name"

docker compose run --rm api school-assistant import-legacy-state `
  --user-email you@example.com `
  --seen-ids /legacy/seen_ids.json `
  --course-ids /legacy/seen_moodle_course_ids.json
```

Compose mounts local `data/` read-only at `/legacy`. The importer is safe to run more than once,
deduplicates using Moodle identifiers, and fails loudly if either source file is missing.

## Run checks without Docker

```powershell
python -m venv venv
venv\Scripts\python -m pip install -e ".[dev]"
venv\Scripts\python -m ruff format --check packages apps tests migrations
venv\Scripts\python -m ruff check packages apps tests migrations
venv\Scripts\python -m mypy
venv\Scripts\python -m pytest tests -q
```

## Legacy workflows

The original `main.py`, `process_outline.py`, `agents/`, and `connectors/` remain available while
their behavior is moved behind the shared core. Their Moodle, Telegram, and optional Notion
payload semantics have not been changed in Phase 0.

Architecture decisions and agent boundaries live in `docs/`. The implementation contract is
tracked in GitHub Issue #1.

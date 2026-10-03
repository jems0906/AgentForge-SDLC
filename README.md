# AgentForge SDLC

AgentForge is a small workflow control plane for AI-assisted changes to a bundled property-management sample application. It demonstrates task intake, a database-backed worker queue, structured plans, sandbox checks, PR-style review, explicit approval, merge/deploy/rollback tracking, and delivery metrics.

## Run locally

The quickest full-stack path uses Docker Compose and PostgreSQL:

```powershell
docker compose up --build
```

Open `http://localhost:3000`; the API is at `http://localhost:8000` and its OpenAPI page at `http://localhost:8000/docs`. Create a task from **Agent tasks** or start a workflow. The worker prepares a proposal and runs the bundled sample tests; the PR then waits for a human decision.

To run without Docker, use Python 3.11+ and Node 20+:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
$env:PYTHONPATH = "backend"
uvicorn app.main:app --app-dir backend --reload --port 8000
```

In another terminal, set `$env:PYTHONPATH = "backend"` and run `python -m worker.task_runner`. In a third terminal run `cd frontend`, `npm ci`, then `npm run dev`; Vite is available at `http://localhost:5173` and proxies `/api` to port 8000. Local mode defaults to SQLite at `agentforge.db`; setting `DATABASE_URL` switches to PostgreSQL.

## What is included

- Five workflow templates: feature, bug fix, refactor, test coverage, and integration.
- Mock-first provider interface, with optional Claude, OpenAI, and Gemini text-generation adapters configured through server environment variables.
- Task queue and worker, PR proposal/reviewer comments, required human approval, and PR lifecycle transitions.
- Fixed-directory subprocess runner with exact command allowlist, no shell, timeout, bounded output, reduced environment, and log redaction.
- CI-quality API and dashboard for pass rate, lint failures, task outcomes, duration, failed runs, and the 90% test-pass alert.
- A bundled FastAPI property-management repo with Property, Tenant, Lease, MaintenanceTicket, and RentPayment models, REST routes, services, and tests.
- Railway service configuration, Dockerfiles, local PostgreSQL Compose stack, and GitHub Actions checks.

## Security and current limits

The executor accepts only exact allowlisted commands and always uses `sample_repo` as its working directory. It does not accept repository uploads or arbitrary shell arguments. This is a constrained runner for a bundled trusted demo, **not** a hostile-code OS/container sandbox; do not run untrusted repositories with it. Production isolation, network egress controls, and per-run disposable containers require a dedicated runner service.

The mock provider never edits files. Remote providers return a proposed diff for review; this MVP does not apply the diff to the sample repo. Approval is blocked unless sandbox tests passed. API keys are read only by the API/worker processes and are never exposed by the frontend.

## Tests

```powershell
$env:PYTHONPATH = "backend"
python -m pytest -q backend/tests
python -m pytest -q
```

The second test command should run from `sample_repo`. Frontend production build: `cd frontend; npm ci; npm run build`.

## Railway deployment

Create four Railway services from this repository and set the repository root directory to `/` for each:

1. **PostgreSQL:** add a Railway-managed PostgreSQL database.
2. **API:** select `railway.json`; provide the database `DATABASE_URL` reference and optionally `CORS_ORIGINS`.
3. **Worker:** select `railway.worker.json`; set the same `DATABASE_URL` and any provider keys used by tasks.
4. **Frontend:** select `railway.frontend.json`; set build variable `VITE_API_URL` to the public API origin, for example `https://agentforge-api.up.railway.app`.

Set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY` only on the API and worker services. Optional model overrides are `ANTHROPIC_MODEL`, `OPENAI_MODEL`, and `GEMINI_MODEL`. Mock remains the default and requires no secrets. Railway configuration files are per-service because a single Railway config file describes one service; service variables and PostgreSQL are attached in the Railway project.

## API overview

- `GET /api/health`, `GET /api/tasks`, `POST /api/tasks`, `POST /api/agents/run`
- `GET /api/workflows`, `GET /api/workflows/runs`, `POST /api/workflows/{template_id}/run`
- `GET /api/reviews`, `POST /api/reviews/{review_id}/decision`
- `GET /api/sandbox/commands`, `POST /api/sandbox/execute`, `GET /api/sandbox/runs`
- `GET /api/providers`, `GET /api/dashboards/ci-quality`

Review decisions are `approve`, `request_changes`, `reject`, `merge`, `deploy`, and `rollback`, with state checks preventing out-of-order transitions.

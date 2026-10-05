- Per-task code changes and diffs, with allowlisted checks executed in disposable, non-root, no-network Docker containers.
- Optional GitHub draft PR creation and approved-PR merging, plus Railway deployment/rollback API integrations.
The executor accepts exact allowlisted commands and only packages the bundled `sample_repo` or its per-task copy. Local checks use shell-free Docker CLI calls and ephemeral non-root containers with no network, read-only source, dropped capabilities, resource limits, timeouts, and bounded/redacted output. Railway uses disposable Railway Sandbox VMs with private-network isolation. Railway's `ISOLATED` mode still permits outbound internet access, so it is not equivalent to Docker's `--network=none`; sandbox compute and dependency downloads may incur usage charges.
The mock provider generates deterministic file contents for common sample tasks. Provider output is validated and applied only to a per-task copy; tests run against that copy. When configured, GitHub receives a draft PR with the validated change under `sample_repo/`; merge calls GitHub only after human approval. API keys stay server-side.
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

Build the sandbox base image once with `docker build --tag agentforge-sample-runner:latest --file sample_repo/Dockerfile.sandbox-base .`. In another terminal, set `$env:PYTHONPATH = "backend"` and run `python -m worker.task_runner`. In a third terminal run `cd frontend`, `npm ci`, then `npm run dev`; Vite is available at `http://localhost:5173` and proxies `/api` to port 8000. Local mode defaults to SQLite at `agentforge.db`; setting `DATABASE_URL` switches to PostgreSQL.

## What is included

- Five workflow templates: feature, bug fix, refactor, test coverage, and integration.
- Mock-first provider interface, with optional Claude, OpenAI, and Gemini text-generation adapters configured through server environment variables.
- Task queue and worker, PR proposal/reviewer comments, required human approval, and PR lifecycle transitions.
- Per-task code changes applied only to isolated worktrees, real diff previews, and tests before review.
- Disposable local Docker checks with no network and Railway Sandbox checks with private-network isolation, bounded logs, and timeouts.
- Optional GitHub draft PR creation/merge and Railway deploy/rollback integrations.
- CI-quality API and dashboard for pass rate, lint failures, task outcomes, duration, failed runs, and the 90% test-pass alert.
- A bundled FastAPI property-management repo with Property, Tenant, Lease, MaintenanceTicket, and RentPayment models, REST routes, services, and tests.
- Railway IaC project definition, service Dockerfiles, local PostgreSQL Compose stack, and GitHub Actions checks.

## Security and current limits

The executor accepts only exact allowlisted commands and packages only the bundled repository or its per-task copy. Local checks run in disposable non-root containers with no network, read-only source, dropped capabilities, memory/CPU/PID limits, an enforced timeout, and bounded/redacted output. Railway checks run in disposable Sandbox VMs with private-network isolation; outbound internet access remains available. Do not treat Railway's isolation setting as a no-egress boundary.

The mock provider generates deterministic changes for common sample tasks. Provider output is path/size-validated, applied only to a per-task copy, and tested there. With GitHub configured, AgentForge opens a draft PR containing the validated changes under `sample_repo/`; only an approved PR is merged. API keys stay server-side.

## Tests

```powershell
$env:PYTHONPATH = "backend"
python -m pytest -q backend/tests
python -m pytest -q
```

The second test command should run from `sample_repo`. Frontend production build: `cd frontend; npm ci; npm run build`.

## Railway deployment

The dedicated Railway project **AgentForge SDLC** is provisioned with managed PostgreSQL plus `api`, `worker`, and `frontend` services. The public app is [frontend-production-a97b.up.railway.app](https://frontend-production-a97b.up.railway.app); API traffic is proxied privately from Nginx to `api.railway.internal`. The API itself has no public domain. Infrastructure is defined in `.railway/railway.ts`; preview changes with `railway config plan` and apply reviewed changes with `railway config apply`.

The current images were uploaded from this local worktree with `railway up`. The Railway services are not connected to GitHub autodeploy yet, and this latest code iteration is still uncommitted/unpushed. After publishing it to `main`, connect the three services to `jems0906/AgentForge-SDLC` if you want GitHub-triggered deployments.

**Before tasks can run in Railway:** set `RAILWAY_PROJECT_TOKEN` on both the API and worker services. Use an environment-scoped project token and keep it in Railway's sealed variables; `RAILWAY_ENVIRONMENT_ID` is already configured by IaC. Until the token is set, the worker leaves jobs queued, the API returns 503 for task creation, and the UI disables task/workflow launch. Each run creates a disposable Railway Sandbox and installs the sample test dependencies, so compute and package downloads can incur usage charges.

**Optional integrations:** set a fine-grained `GITHUB_TOKEN` on API/worker for draft PR creation and merge. The same `RAILWAY_PROJECT_TOKEN` enables sandbox execution on both services and Railway deploy/rollback actions on API. Provider keys for Claude/OpenAI/Gemini belong only on API/worker. Enter secrets in Railway's variable settings; do not commit or paste them into chat.

The managed Postgres volume currently has 50 GB allocated (about 8 MB used at provisioning). Check Railway usage before leaving the demo running; usage-based cloud charges may apply.

## API overview

- `GET /api/health`, `GET /api/tasks`, `POST /api/tasks`, `POST /api/agents/run`
- `GET /api/workflows`, `GET /api/workflows/runs`, `POST /api/workflows/{template_id}/run`
- `GET /api/reviews`, `POST /api/reviews/{review_id}/decision`
- `GET /api/sandbox/commands`, `POST /api/sandbox/execute`, `GET /api/sandbox/runs`
- `GET /api/providers`, `GET /api/integrations`, `GET /api/dashboards/ci-quality`

Review decisions are `approve`, `request_changes`, `reject`, `merge`, `deploy`, and `rollback`, with state checks preventing out-of-order transitions.

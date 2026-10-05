# Workflow design

Workflow templates are immutable descriptions in `backend/app/orchestrator/workflow_templates.py`. A task type selects a template, creates a queued `WorkflowExecution`, and is picked up by the worker. The worker records a structured plan, applies validated proposed file contents to a per-task worktree, runs Docker-isolated tests, and creates a diff/review before pausing at the approval step. When GitHub credentials are present it also opens a draft PR from the tested files.

The local lifecycle is `queued -> running -> in_review -> approved -> merged -> deployed`. Review actions can also end at `changes_requested`, `rejected`, or `rolled_back`. Approval requires passing sandbox tests. If GitHub is configured, merge calls the GitHub API; if Railway is configured, deploy waits for a new successful deployment and rollback checks Railway eligibility before issuing the rollback mutation. Without credentials the UI marks these actions unavailable.

Feature, bug-fix, refactor, test-coverage, and integration workflows are available. A workflow run is started via `POST /api/workflows/{template_id}/run` with a task title and description.

# Workflow design

Workflow templates are immutable descriptions in `backend/app/orchestrator/workflow_templates.py`. A task type selects a template, creates a queued `WorkflowExecution`, and is picked up by the worker. The worker records completed planning, implementation-proposal, and test steps, then pauses on the approval step.

The lifecycle is `queued -> running -> in_review -> approved -> merged -> deployed`. Review actions can also end at `changes_requested`, `rejected`, or `rolled_back`. Approval requires a passing sandbox test result. Requesting changes appends the human note to the task instructions and requeues it. Deploy and rollback are explicit recorded decisions; this demo does not perform a real deployment.

Feature, bug-fix, refactor, test-coverage, and integration workflows are available. A workflow run is started via `POST /api/workflows/{template_id}/run` with a task title and description.

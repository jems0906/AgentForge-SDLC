# CI quality metrics

- **Test pass rate:** passed sandbox executions divided by all recorded sandbox executions; a threshold alert is emitted below 90%.
- **Lint failures:** failed or timed-out `ruff check` runs.
- **Agent success rate:** approved, merged, and deployed tasks divided by those tasks plus failed tasks.
- **Average task time:** mean duration from worker start through review preparation for tasks with both timestamps.
- **Failed runs:** sandbox commands that fail or time out.
- **Rollback count:** explicit rollback decisions, recorded as quality metrics.

The dashboard API is `GET /api/dashboards/ci-quality`. These demo metrics are derived from application records and should not be treated as a substitute for a production metrics/alerting service.

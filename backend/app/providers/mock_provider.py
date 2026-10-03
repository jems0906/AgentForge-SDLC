class MockProvider:
    name = "mock"

    def generate_plan(self, task: dict) -> list[dict]:
        task_type = task.get("task_type", "feature")
        return [
            {"title": "Inspect the property-management domain", "detail": "Trace the existing model and API behavior relevant to this request."},
            {"title": "Implement a focused change", "detail": f"Apply the smallest {task_type} change and preserve existing contracts."},
            {"title": "Validate and prepare review", "detail": "Run the sample repository tests and prepare a review summary."},
        ]

    def generate_code(self, task: dict, plan: list[dict]) -> dict:
        return {
            "summary": f"Prepared a mock implementation plan for: {task['title']}",
            "diff": "# Mock provider\n# No files were modified. Connect a configured coding agent to produce a patch.\n",
            "files_changed": [],
        }

    def review_code(self, diff: str) -> list[dict]:
        return [{"severity": "info", "file": "workflow", "line": None, "comment": "Human review is required before any proposed change ships."}]

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
        task_text = f"{task.get('title', '')} {task.get('description', '')}".lower()
        context = task.get("code_context", {})
        if "priority" in task_text:
            content = """PRIORITY_ALIASES = {"critical": "urgent"}
PRIORITY_RANK = {"low": 1, "normal": 2, "high": 3, "urgent": 4}


def normalize_priority(priority: str) -> str:
    normalized = priority.strip().lower()
    normalized = PRIORITY_ALIASES.get(normalized, normalized)
    if normalized not in PRIORITY_RANK:
        raise ValueError("Priority must be low, normal, high, or urgent")
    return normalized
"""
            path = "app/services/maintenance.py"
            summary = "Accept the property-management 'critical' priority as the existing urgent level."
        elif "lease" in task_text or "renewal" in task_text:
            content = """from datetime import date

from app.services.notification_service import lease_renewal_due


def leases_requiring_renewal(leases: list[dict], today: date, notice_days: int = 60) -> list[dict]:
    return [
        lease for lease in leases
        if lease_renewal_due(lease["ends_on"], today=today, notice_days=notice_days)
    ]
"""
            path = "app/services/renewal_reminders.py"
            summary = "Add a reusable selector for leases entering the renewal notice window."
        elif "payment" in task_text:
            content = """def validate_rent_payment(amount: int, monthly_rent: int) -> bool:
    if isinstance(amount, bool) or isinstance(monthly_rent, bool):
        return False
    if not isinstance(amount, int) or not isinstance(monthly_rent, int):
        return False
    if amount <= 0 or monthly_rent <= 0:
        return False
    return amount <= monthly_rent * 2
"""
            path = "app/services/payment_validation.py"
            summary = "Make rent validation reject invalid runtime types and non-positive rent values."
        elif "test" in task_text:
            content = """from app.services.maintenance import normalize_priority


def test_priority_whitespace_and_case_are_normalized():
    assert normalize_priority(" URGENT ") == "urgent"
"""
            path = "tests/test_generated_priority_case.py"
            summary = "Add a focused boundary test for maintenance-priority normalization."
        else:
            content = """from typing import Protocol


class PaymentProvider(Protocol):
    def charge(self, amount: int, currency: str) -> str: ...
"""
            path = "app/services/payment_provider.py"
            summary = "Define a minimal provider boundary for third-party rent-payment integrations."
        if path in context and context[path] == content:
            return {"summary": "The bundled mock change is already present; no code change was proposed.", "files": []}
        return {
            "summary": summary,
            "files": [{"path": path, "content": content}],
        }

    def review_code(self, diff: str) -> list[dict]:
        return [{"severity": "info", "file": "workflow", "line": None, "comment": "Human review is required before any proposed change ships."}]

from datetime import date, datetime, timedelta, timezone


def lease_renewal_due(ends_on: date, today: date | None = None, notice_days: int = 60) -> bool:
    current_day = today or datetime.now(timezone.utc).date()
    return current_day <= ends_on <= current_day + timedelta(days=notice_days)

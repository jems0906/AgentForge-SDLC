from datetime import date, timedelta


def lease_renewal_due(ends_on: date, today: date | None = None, notice_days: int = 60) -> bool:
    current_day = today or date.today()
    return current_day <= ends_on <= current_day + timedelta(days=notice_days)

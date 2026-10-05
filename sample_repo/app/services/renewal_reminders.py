from datetime import date

from app.services.notification_service import lease_renewal_due


def leases_requiring_renewal(leases: list[dict], today: date, notice_days: int = 60) -> list[dict]:
    return [
        lease for lease in leases
        if lease_renewal_due(lease["ends_on"], today=today, notice_days=notice_days)
    ]

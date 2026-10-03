from datetime import date

import pytest

from app.services.maintenance import normalize_priority
from app.services.notification_service import lease_renewal_due
from app.services.payment_validation import validate_rent_payment


def test_rent_payment_rejects_nonpositive_and_caps_overpayment():
    assert not validate_rent_payment(0, 1200)
    assert not validate_rent_payment(2500, 1200)
    assert validate_rent_payment(1200, 1200)


def test_lease_renewal_notice_window_is_inclusive():
    today = date(2026, 1, 1)
    assert lease_renewal_due(date(2026, 3, 2), today)
    assert not lease_renewal_due(date(2026, 3, 3), today)


def test_maintenance_priority_is_normalized_and_validated():
    assert normalize_priority(" URGENT ") == "urgent"
    with pytest.raises(ValueError):
        normalize_priority("whenever")

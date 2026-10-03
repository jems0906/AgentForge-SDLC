from app.sandbox.executor import redact


def test_redacts_common_secret_assignments():
    assert redact("API_KEY=super-secret") == "API_KEY=[REDACTED]"

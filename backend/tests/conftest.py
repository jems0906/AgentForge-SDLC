import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


test_db = Path(__file__).parent / "test-agentforge.db"
os.environ["DATABASE_URL"] = f"sqlite:///{test_db}"

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if test_db.exists():
        test_db.unlink()

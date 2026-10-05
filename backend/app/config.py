import os
from pathlib import Path
import tempfile


ROOT_DIR = Path(os.getenv("AGENTFORGE_ROOT", Path(__file__).resolve().parents[2]))
SAMPLE_REPO = ROOT_DIR / "sample_repo"
RUNS_DIR = Path(os.getenv("AGENTFORGE_RUNS_DIR", str(Path(tempfile.gettempdir()) / "agentforge-runs")))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'agentforge.db'}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

APP_ENV = os.getenv("APP_ENV", "development")
SANDBOX_TIMEOUT_SECONDS = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "30"))

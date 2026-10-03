import os
import re
import subprocess
import time

from app.config import SAMPLE_REPO, SANDBOX_TIMEOUT_SECONDS
from app.sandbox.allowlist import COMMANDS


SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|token|password|secret)(\s*[=:]\s*)([^\s,;]+)")


def redact(text: str) -> str:
    return SECRET_PATTERN.sub(r"\1\2[REDACTED]", text)


def execute(command: str) -> dict:
    if command not in COMMANDS:
        raise ValueError(f"Command is not allowlisted. Choose one of: {', '.join(COMMANDS)}")
    if not SAMPLE_REPO.is_dir():
        raise RuntimeError("Bundled sample repository is unavailable.")
    started = time.monotonic()
    environment = {key: value for key, value in os.environ.items() if key in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
    try:
        result = subprocess.run(
            COMMANDS[command], cwd=SAMPLE_REPO, env=environment,
            capture_output=True, text=True, timeout=SANDBOX_TIMEOUT_SECONDS,
            shell=False, check=False,
        )
        return {
            "status": "passed" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "stdout": redact(result.stdout[-12000:]),
            "stderr": redact(result.stderr[-12000:]),
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    except subprocess.TimeoutExpired as error:
        return {
            "status": "timeout", "exit_code": None,
            "stdout": redact((error.stdout or "")[-12000:] if isinstance(error.stdout, str) else ""),
            "stderr": "Command timed out.",
            "duration_seconds": round(time.monotonic() - started, 3),
        }

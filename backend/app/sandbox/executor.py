import io
import json
import os
import re
import subprocess
import tarfile
import time
import uuid
from pathlib import Path

from app.config import APP_ENV, RUNS_DIR, SAMPLE_REPO, SANDBOX_TIMEOUT_SECONDS
from app.sandbox.allowlist import COMMANDS


SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|token|password|secret)(\s*[=:]\s*)([^\s,;]+)")
SANDBOX_BASE_IMAGE = "agentforge-sample-runner:latest"
MAX_CONTEXT_BYTES = 12_000_000
MAX_LOG_BYTES = 12_000
IGNORED_CONTEXT = {"__pycache__", ".pytest_cache", ".ruff_cache", ".git"}
RAILWAY_RUNNER = Path(__file__).resolve().parents[2] / "sandbox_runner" / "execute.mjs"


def redact(text: str) -> str:
    return SECRET_PATTERN.sub(r"\1\2[REDACTED]", text)


def _build_context(repo: Path) -> io.BytesIO:
    archive = io.BytesIO()
    total_bytes = 0
    with tarfile.open(fileobj=archive, mode="w") as bundle:
        dockerfile = b"FROM agentforge-sample-runner:latest\nWORKDIR /workspace\nCOPY --chown=65534:65534 . /workspace\nUSER 65534:65534\n"
        docker_info = tarfile.TarInfo("Dockerfile.agentforge")
        docker_info.size = len(dockerfile)
        bundle.addfile(docker_info, io.BytesIO(dockerfile))
        for path in sorted(repo.rglob("*")):
            relative = path.relative_to(repo)
            if not path.is_file() or path.is_symlink() or any(part in IGNORED_CONTEXT for part in relative.parts):
                continue
            if path.suffix not in {".py", ".txt", ".md", ".toml", ".ini", ".cfg"}:
                continue
            data = path.read_bytes()
            total_bytes += len(data)
            if total_bytes > MAX_CONTEXT_BYTES:
                raise ValueError("Task workspace exceeds the sandbox image size limit.")
            info = tarfile.TarInfo(relative.as_posix())
            info.size = len(data)
            info.mode = 0o444
            bundle.addfile(info, io.BytesIO(data))
    archive.seek(0)
    return archive


def _docker_environment() -> dict[str, str]:
    allowed = {
        "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "USERPROFILE", "HOME",
        "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CERT_PATH", "DOCKER_TLS_VERIFY",
    }
    return {key: value for key, value in os.environ.items() if key in allowed}


def _docker(command: list[str], timeout: int, context: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", *command], input=context, capture_output=True,
        timeout=timeout, check=False, shell=False, env=_docker_environment(),
    )


def _execute_docker(command: str, repo_path: Path | None = None) -> dict:
    if command not in COMMANDS:
        raise ValueError(f"Command is not allowlisted. Choose one of: {', '.join(COMMANDS)}")
    workdir = (repo_path or SAMPLE_REPO).resolve()
    allowed_roots = (SAMPLE_REPO.resolve(), RUNS_DIR.resolve())
    if not workdir.is_dir() or not any(workdir == root or root in workdir.parents for root in allowed_roots):
        raise RuntimeError("Sandbox source must be the bundled repository or an AgentForge task copy.")
    started = time.monotonic()
    tag = f"agentforge-task-{uuid.uuid4().hex}"
    image_built = False
    try:
        build_context = _build_context(workdir).getvalue()
        try:
            build = _docker(["build", "--quiet", "--network=none", "--tag", tag, "--file", "Dockerfile.agentforge", "-"], timeout=90, context=build_context)
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "exit_code": None, "stdout": "", "stderr": "Sandbox image build timed out.", "duration_seconds": round(time.monotonic() - started, 3)}
        if build.returncode != 0:
            return {"status": "failed", "exit_code": build.returncode, "stdout": "", "stderr": redact(build.stderr.decode("utf-8", errors="replace")[-MAX_LOG_BYTES:]), "duration_seconds": round(time.monotonic() - started, 3)}
        image_built = True
        environment = [
            "--env", "PYTHONDONTWRITEBYTECODE=1",
            "--env", "SAMPLE_DATABASE_URL=sqlite://",
            "--env", "RUFF_CACHE_DIR=/tmp/ruff-cache",
        ]
        runtime_flags = [
            "create", "--name", tag, "--log-driver=json-file", "--log-opt", "max-size=1m",
            "--log-opt", "max-file=1", "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--pids-limit=64", "--memory=256m",
            "--cpus=0.5", "--user=65534:65534",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--workdir=/workspace",
            *environment, tag, *COMMANDS[command],
        ]
        created = _docker(runtime_flags, timeout=30)
        if created.returncode != 0:
            return {"status": "failed", "exit_code": created.returncode, "stdout": "", "stderr": redact(created.stderr.decode("utf-8", errors="replace")[-MAX_LOG_BYTES:]), "duration_seconds": round(time.monotonic() - started, 3)}
        image_built = True
        started_container = _docker(["start", tag], timeout=15)
        if started_container.returncode != 0:
            return {"status": "failed", "exit_code": started_container.returncode, "stdout": "", "stderr": redact(started_container.stderr.decode("utf-8", errors="replace")[-MAX_LOG_BYTES:]), "duration_seconds": round(time.monotonic() - started, 3)}
        try:
            result = _docker(["wait", tag], timeout=SANDBOX_TIMEOUT_SECONDS)
            exit_code = int(result.stdout.strip() or "125")
            status = "passed" if result.returncode == 0 and exit_code == 0 else "failed"
        except subprocess.TimeoutExpired as error:
            _docker(["kill", tag], timeout=10)
            status, exit_code = "timeout", None
        logs = _docker(["logs", "--tail", "200", tag], timeout=10)
        stdout = redact(logs.stdout.decode("utf-8", errors="replace")[-MAX_LOG_BYTES:])
        stderr = redact(logs.stderr.decode("utf-8", errors="replace")[-MAX_LOG_BYTES:])
        if status == "timeout":
            stderr = (stderr + "\nSandbox command timed out and its container was terminated.").strip()
        return {
            "status": status,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    except (OSError, ValueError) as error:
        return {
            "status": "failed", "exit_code": None, "stdout": "",
            "stderr": redact(f"Isolated Docker runner unavailable: {error}")[-MAX_LOG_BYTES:],
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    finally:
        if image_built:
            try:
                _docker(["rm", "--force", tag], timeout=15)
                _docker(["image", "rm", "--force", tag], timeout=15)
            except (OSError, subprocess.TimeoutExpired):
                pass


def _execute_railway(command: str, repo_path: Path) -> dict:
    token = os.getenv("RAILWAY_PROJECT_TOKEN")
    environment_id = os.getenv("RAILWAY_ENVIRONMENT_ID")
    if not token or not environment_id:
        return {
            "status": "failed", "exit_code": None, "stdout": "",
            "stderr": "Railway Sandbox requires RAILWAY_PROJECT_TOKEN and RAILWAY_ENVIRONMENT_ID.",
            "duration_seconds": 0,
        }
    if not RAILWAY_RUNNER.is_file():
        raise RuntimeError("Railway Sandbox runner package is missing from this service image.")

    files = []
    total_bytes = 0
    for path in sorted(repo_path.rglob("*.py")):
        relative = path.relative_to(repo_path)
        if path.is_symlink() or any(part in IGNORED_CONTEXT for part in relative.parts):
            continue
        if not relative.parts or relative.parts[0] not in {"app", "tests"}:
            continue
        content = path.read_text(encoding="utf-8")
        file_size = len(content.encode("utf-8"))
        total_bytes += file_size
        if file_size > 256_000 or total_bytes > MAX_CONTEXT_BYTES:
            return {
                "status": "failed", "exit_code": None, "stdout": "",
                "stderr": "Railway Sandbox source exceeds the configured file-size limits.",
                "duration_seconds": 0,
            }
        files.append({"path": relative.as_posix(), "content": content})
    runner_environment = {
        "PATH": os.getenv("PATH", ""),
        "RAILWAY_PROJECT_TOKEN": token,
        "RAILWAY_ENVIRONMENT_ID": environment_id,
    }
    started = time.monotonic()
    try:
        result = subprocess.run(
            ["node", str(RAILWAY_RUNNER)],
            input=json.dumps({"command": command, "files": files, "timeoutSeconds": SANDBOX_TIMEOUT_SECONDS}),
            capture_output=True, text=True, timeout=300, check=False,
            shell=False, env=runner_environment,
        )
        output = json.loads(result.stdout)
        output["stdout"] = redact(str(output.get("stdout", ""))[-MAX_LOG_BYTES:])
        output["stderr"] = redact(str(output.get("stderr", ""))[-MAX_LOG_BYTES:])
        output["duration_seconds"] = round(time.monotonic() - started, 3)
        return output
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        return {
            "status": "timeout" if isinstance(error, subprocess.TimeoutExpired) else "failed",
            "exit_code": None, "stdout": "",
            "stderr": redact(f"Railway Sandbox execution failed: {error}")[-MAX_LOG_BYTES:],
            "duration_seconds": round(time.monotonic() - started, 3),
        }


def execute(command: str, repo_path: Path | None = None) -> dict:
    mode = os.getenv("SANDBOX_MODE", "railway" if APP_ENV == "production" else "docker")
    if mode == "railway":
        workdir = (repo_path or SAMPLE_REPO).resolve()
        allowed_roots = (SAMPLE_REPO.resolve(), RUNS_DIR.resolve())
        if not workdir.is_dir() or not any(workdir == root or root in workdir.parents for root in allowed_roots):
            raise RuntimeError("Sandbox source must be the bundled repository or an AgentForge task copy.")
        if command not in COMMANDS:
            raise ValueError(f"Command is not allowlisted. Choose one of: {', '.join(COMMANDS)}")
        return _execute_railway(command, workdir)
    if mode != "docker":
        raise ValueError("SANDBOX_MODE must be 'docker' or 'railway'.")
    return _execute_docker(command, repo_path)

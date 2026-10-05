import difflib
import shutil
from pathlib import Path, PurePosixPath

from app.config import RUNS_DIR, SAMPLE_REPO


IGNORED_NAMES = {"__pycache__", ".pytest_cache", ".ruff_cache", "property-management.db"}
ALLOWED_ROOTS = {"app", "tests"}
MAX_FILES = 24
MAX_FILE_BYTES = 256_000


def collect_code_context(repo: Path = SAMPLE_REPO) -> dict[str, str]:
    context = {}
    for path in sorted(repo.rglob("*.py")):
        if any(part in IGNORED_NAMES for part in path.parts):
            continue
        relative = path.relative_to(repo).as_posix()
        content = path.read_text(encoding="utf-8")
        context[relative] = content[:12000]
        if sum(map(len, context.values())) > 70000:
            break
    return context


def _checked_path(repo: Path, relative_path: str) -> Path:
    candidate = PurePosixPath(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative_path:
        raise ValueError(f"Unsafe generated path: {relative_path}")
    if not candidate.parts or candidate.parts[0] not in ALLOWED_ROOTS or candidate.suffix != ".py":
        raise ValueError(f"Generated path is outside the Python app/tests allowlist: {relative_path}")
    target = (repo / Path(*candidate.parts)).resolve()
    try:
        target.relative_to(repo.resolve())
    except ValueError as error:
        raise ValueError(f"Generated path escapes the task workspace: {relative_path}") from error
    return target


def prepare_task_workspace(task_id: int, files: list[dict], repo: Path = SAMPLE_REPO) -> tuple[Path, str, list[str]]:
    if not isinstance(files, list) or not files or len(files) > MAX_FILES:
        raise ValueError("The provider must return between 1 and 24 Python file changes.")
    run_root = RUNS_DIR.resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    task_root = (run_root / str(task_id)).resolve()
    task_root.relative_to(run_root)
    if task_root.exists():
        shutil.rmtree(task_root)
    worktree = task_root / "sample_repo"
    shutil.copytree(repo, worktree, ignore=shutil.ignore_patterns(*IGNORED_NAMES, "*.db"))

    patch_parts = []
    changed_paths = []
    seen_paths = set()
    try:
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("content"), str):
                raise ValueError("Each generated change must contain a relative path and complete file content.")
            relative_path = item["path"]
            if relative_path in seen_paths:
                raise ValueError(f"Generated path was repeated: {relative_path}")
            seen_paths.add(relative_path)
            content = item["content"]
            if len(content.encode("utf-8")) > MAX_FILE_BYTES:
                raise ValueError(f"Generated file is too large: {relative_path}")
            target = _checked_path(worktree, relative_path)
            original = target.read_text(encoding="utf-8") if target.is_file() else ""
            if target.exists() and not target.is_file():
                raise ValueError(f"Generated path is not a regular file: {relative_path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")
            patch_parts.extend(difflib.unified_diff(
                original.splitlines(keepends=True), content.splitlines(keepends=True),
                fromfile=f"a/{relative_path}" if original else "/dev/null",
                tofile=f"b/{relative_path}",
            ))
            changed_paths.append(relative_path)
        if not patch_parts:
            raise ValueError("The generated changes do not modify any files.")
        return worktree, "".join(patch_parts), changed_paths
    except Exception:
        shutil.rmtree(task_root, ignore_errors=True)
        raise

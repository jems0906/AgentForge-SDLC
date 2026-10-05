import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


API_ROOT = "https://api.github.com"


def _configuration():
    token = os.getenv("GITHUB_TOKEN")
    repository = os.getenv("GITHUB_REPOSITORY", "")
    owner, separator, name = repository.partition("/")
    if not token or not separator or not owner or not name or "/" in name:
        return None
    return token, repository, os.getenv("GITHUB_BASE_BRANCH", "main")


def is_configured() -> bool:
    return _configuration() is not None


def _request(token: str, method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        f"{API_ROOT}{path}", data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        }, method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError("GitHub request failed; verify repository access and token scopes.") from error


def create_draft_pull_request(task_id: int, title: str, description: str, repo_path: Path, changed_paths: list[str]):
    configuration = _configuration()
    if configuration is None:
        return None
    token, repository, base = configuration
    repo_path = repo_path.resolve()
    encoded_base = urllib.parse.quote(base, safe="")
    reference = _request(token, "GET", f"/repos/{repository}/git/ref/heads/{encoded_base}")
    base_sha = reference["object"]["sha"]
    base_commit = _request(token, "GET", f"/repos/{repository}/git/commits/{base_sha}")
    tree_entries = []
    for relative_path in changed_paths:
        file_path = (repo_path / relative_path).resolve()
        file_path.relative_to(repo_path)
        content = file_path.read_text(encoding="utf-8")
        blob = _request(token, "POST", f"/repos/{repository}/git/blobs", {
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "encoding": "base64",
        })
        tree_entries.append({"path": f"sample_repo/{relative_path}", "mode": "100644", "type": "blob", "sha": blob["sha"]})
    tree = _request(token, "POST", f"/repos/{repository}/git/trees", {
        "base_tree": base_commit["tree"]["sha"], "tree": tree_entries,
    })
    commit = _request(token, "POST", f"/repos/{repository}/git/commits", {
        "message": f"AgentForge: {title[:120]}", "tree": tree["sha"], "parents": [base_sha],
    })
    branch = f"agentforge/task-{task_id}-{uuid.uuid4().hex[:8]}"
    _request(token, "POST", f"/repos/{repository}/git/refs", {
        "ref": f"refs/heads/{branch}", "sha": commit["sha"],
    })
    pull_request = _request(token, "POST", f"/repos/{repository}/pulls", {
        "title": title[:250],
        "body": f"{description[:5000]}\n\nGenerated and tested by AgentForge. Human approval is required before merge.",
        "head": branch,
        "base": base,
        "draft": True,
    })
    return {"repository": repository, "number": pull_request["number"], "url": pull_request["html_url"], "branch": branch, "head_sha": commit["sha"]}


def merge_pull_request(pull_request: dict) -> dict:
    configuration = _configuration()
    if configuration is None:
        raise RuntimeError("Configure GITHUB_TOKEN and GITHUB_REPOSITORY to merge a real GitHub pull request.")
    token, repository, _ = configuration
    if pull_request.get("repository") != repository or not pull_request.get("number"):
        raise RuntimeError("The pull request does not belong to the configured GitHub repository.")
    result = _request(token, "PUT", f"/repos/{repository}/pulls/{int(pull_request['number'])}/merge", {"merge_method": "squash"})
    if not result.get("merged"):
        raise RuntimeError("GitHub did not merge the pull request.")
    return {"merged": True, "sha": result.get("sha"), "message": result.get("message", "")}

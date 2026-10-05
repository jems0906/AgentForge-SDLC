from pathlib import Path

import pytest

from app.integrations import github, railway


def test_github_draft_pr_uses_generated_worktree_files(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/property-app")
    source = tmp_path / "app" / "feature.py"
    source.parent.mkdir()
    source.write_text("VALUE = 42\n", encoding="utf-8")
    calls = []

    def fake_request(token, method, path, body=None):
        calls.append((method, path, body))
        if path.endswith("/git/ref/heads/main"):
            return {"object": {"sha": "base-sha"}}
        if path.endswith("/git/commits/base-sha"):
            return {"tree": {"sha": "base-tree"}}
        if path.endswith("/git/blobs"):
            return {"sha": "blob-sha"}
        if path.endswith("/git/trees"):
            return {"sha": "tree-sha"}
        if path.endswith("/git/commits"):
            return {"sha": "commit-sha"}
        if path.endswith("/git/refs"):
            return {}
        if path.endswith("/pulls"):
            return {"number": 9, "html_url": "https://github.com/owner/property-app/pull/9"}
        raise AssertionError(path)

    monkeypatch.setattr(github, "_request", fake_request)
    result = github.create_draft_pull_request(4, "Add a feature", "details", tmp_path, ["app/feature.py"])

    assert result["number"] == 9
    assert result["repository"] == "owner/property-app"
    assert calls[-1][2]["draft"] is True
    assert calls[2][2]["content"]
    assert calls[3][2]["tree"][0]["path"] == "sample_repo/app/feature.py"


def test_github_merge_requires_configuration(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
        github.merge_pull_request({"number": 1})


def test_railway_deploy_requires_service_configuration(monkeypatch):
    for name in ("RAILWAY_PROJECT_TOKEN", "RAILWAY_TOKEN", "RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_ID", "RAILWAY_SERVICE_ID"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError, match="Railway token"):
        railway.deploy()


def test_railway_deploy_waits_for_a_new_successful_deployment(monkeypatch):
    configuration = ("Project-Access-Token", "test-token", "project", "environment", "service")
    monkeypatch.setattr(railway, "_configuration", lambda: configuration)

    def fake_graphql(query, variables, supplied_configuration=None):
        if "environmentTriggersDeploy" in query:
            return {"environmentTriggersDeploy": True}
        if "first: $first" in query and "createdAt" not in query:
            return {"deployments": {"edges": [{"node": {"id": "old-deployment"}}]}}
        return {"deployments": {"edges": [{"node": {"id": "new-deployment", "status": "SUCCESS", "url": "https://app.example", "createdAt": "now"}}]}}

    monkeypatch.setattr(railway, "_graphql", fake_graphql)
    result = railway.deploy()

    assert result["id"] == "new-deployment"
    assert result["status"] == "SUCCESS"


def test_railway_rollback_rejects_ineligible_target(monkeypatch):
    configuration = ("Project-Access-Token", "test-token", "project", "environment", "service")
    monkeypatch.setattr(railway, "_configuration", lambda: configuration)

    def fake_graphql(query, variables, supplied_configuration=None):
        if "deployment(id:" in query:
            return {"deployment": {"id": "old-deployment", "canRollback": False}}
        return {"deployments": {"edges": [
            {"node": {"id": "latest", "status": "SUCCESS"}},
            {"node": {"id": "old-deployment", "status": "SUCCESS"}},
        ]}}

    monkeypatch.setattr(railway, "_graphql", fake_graphql)
    with pytest.raises(RuntimeError, match="cannot be rolled back"):
        railway.rollback()

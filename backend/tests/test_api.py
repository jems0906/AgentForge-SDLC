def test_health_and_workflow_catalog(client):
    assert client.get("/api/health").json()["status"] == "ok"
    assert {item["id"] for item in client.get("/api/workflows").json()} == {"feature", "bugfix", "refactor", "test", "integration"}


def test_server_launcher_reads_port_from_environment(monkeypatch):
    import app.serve

    launched = {}
    monkeypatch.setenv("PORT", "9123")
    monkeypatch.setattr(app.serve.uvicorn, "run", lambda app, **kwargs: launched.update(kwargs))
    app.serve.main()
    assert launched == {"host": "0.0.0.0", "port": 9123}


def test_task_creation_queues_workflow(client):
    response = client.post("/api/tasks", json={"title": "Fix ticket priority", "description": "Normalize priority", "task_type": "bugfix"})
    assert response.status_code == 201
    task = response.json()
    assert task["status"] == "queued"
    assert task["workflow_id"]
    assert client.get("/api/workflows/runs").json()[0]["template_id"] == "bugfix"


def test_provider_requires_a_real_configured_adapter(client):
    response = client.post("/api/tasks", json={"title": "Connect payments", "provider": "anthropic"})
    assert response.status_code == 422


def test_production_tasks_wait_for_railway_sandbox_token(client, monkeypatch):
    monkeypatch.setattr("app.main.APP_ENV", "production")
    monkeypatch.delenv("SANDBOX_MODE", raising=False)
    monkeypatch.delenv("RAILWAY_PROJECT_TOKEN", raising=False)
    response = client.post("/api/tasks", json={"title": "Add lease renewal reminders"})
    assert response.status_code == 503
    assert "RAILWAY_PROJECT_TOKEN" in response.json()["detail"]


def test_production_tasks_queue_with_railway_sandbox_token(client, monkeypatch):
    monkeypatch.setattr("app.main.APP_ENV", "production")
    monkeypatch.setenv("SANDBOX_MODE", "railway")
    monkeypatch.setenv("RAILWAY_PROJECT_TOKEN", "test-project-token")
    response = client.post("/api/tasks", json={"title": "Add lease renewal reminders"})
    assert response.status_code == 201
    assert response.json()["status"] == "queued"


def test_sandbox_rejects_commands_outside_allowlist(client):
    response = client.post("/api/sandbox/execute", json={"command": "python -c print(1)"})
    assert response.status_code == 400
    assert "not allowlisted" in response.json()["detail"]


def test_review_transitions_require_human_gate(client, monkeypatch):
    task = client.post("/api/tasks", json={"title": "Add renewal reminders"}).json()
    from app.database import SessionLocal
    from app.models import AgentTask, CodeReview

    with SessionLocal() as db:
        agent_task = db.get(AgentTask, task["id"])
        agent_task.outputs = {"tests": {"status": "passed"}, "github": {"repository": "owner/repo", "number": 1}}
        review = CodeReview(task_id=task["id"], status="review", summary="Ready", diff="diff")
        db.add(review)
        db.commit()
        review_id = review.id
    assert client.post(f"/api/reviews/{review_id}/decision", json={"decision": "merge"}).status_code == 409
    assert client.post(f"/api/reviews/{review_id}/decision", json={"decision": "approve"}).json()["status"] == "approved"
    monkeypatch.setattr("app.main.github_configured", lambda: True)
    monkeypatch.setattr("app.main.merge_pull_request", lambda pull_request: {"merged": True, "sha": "merge-sha"})
    assert client.post(f"/api/reviews/{review_id}/decision", json={"decision": "merge"}).json()["status"] == "merged"


def test_merge_requires_github_pr_configuration(client):
    from app.database import SessionLocal
    from app.models import AgentTask, CodeReview

    task = client.post("/api/tasks", json={"title": "Merge a reviewed task"}).json()
    with SessionLocal() as db:
        db.get(AgentTask, task["id"]).status = "approved"
        review = CodeReview(task_id=task["id"], status="approved", summary="ready", diff="diff")
        db.add(review)
        db.commit()
        review_id = review.id
    response = client.post(f"/api/reviews/{review_id}/decision", json={"decision": "merge"})
    assert response.status_code == 502
    assert "GitHub credentials" in response.json()["detail"]


def test_deployment_requires_railway_configuration(client, monkeypatch):
    from app.database import SessionLocal
    from app.models import AgentTask, CodeReview

    task = client.post("/api/tasks", json={"title": "Deploy a property API"}).json()
    with SessionLocal() as db:
        db.get(AgentTask, task["id"]).status = "merged"
        review = CodeReview(task_id=task["id"], status="merged", summary="ready", diff="diff")
        db.add(review)
        db.commit()
        review_id = review.id
    monkeypatch.delenv("RAILWAY_PROJECT_TOKEN", raising=False)
    monkeypatch.delenv("RAILWAY_TOKEN", raising=False)
    response = client.post(f"/api/reviews/{review_id}/decision", json={"decision": "deploy"})
    assert response.status_code == 502
    assert "Railway" in response.json()["detail"]

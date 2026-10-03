def test_health_and_workflow_catalog(client):
    assert client.get("/api/health").json()["status"] == "ok"
    assert {item["id"] for item in client.get("/api/workflows").json()} == {"feature", "bugfix", "refactor", "test", "integration"}


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


def test_sandbox_rejects_commands_outside_allowlist(client):
    response = client.post("/api/sandbox/execute", json={"command": "python -c print(1)"})
    assert response.status_code == 400
    assert "not allowlisted" in response.json()["detail"]


def test_review_transitions_require_human_gate(client):
    task = client.post("/api/tasks", json={"title": "Add renewal reminders"}).json()
    from app.database import SessionLocal
    from app.models import AgentTask, CodeReview

    with SessionLocal() as db:
        agent_task = db.get(AgentTask, task["id"])
        agent_task.outputs = {"tests": {"status": "passed"}}
        review = CodeReview(task_id=task["id"], status="review", summary="Ready", diff="diff")
        db.add(review)
        db.commit()
        review_id = review.id
    assert client.post(f"/api/reviews/{review_id}/decision", json={"decision": "merge"}).status_code == 409
    assert client.post(f"/api/reviews/{review_id}/decision", json={"decision": "approve"}).json()["status"] == "approved"
    assert client.post(f"/api/reviews/{review_id}/decision", json={"decision": "merge"}).json()["status"] == "merged"

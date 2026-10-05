def test_worker_processes_task_through_review(client):
    task = client.post("/api/tasks", json={"title": "Add vendor gateway contract"}).json()

    from worker.task_runner import process_one

    assert process_one()
    completed = client.get(f"/api/tasks/{task['id']}").json()
    assert completed["status"] == "in_review"
    assert completed["outputs"]["tests"]["status"] == "passed"
    assert completed["outputs"]["proposal"]["files_changed"]
    assert "No files were modified" not in completed["outputs"]["proposal"]["diff"]
    reviews = client.get("/api/reviews").json()
    assert len(reviews) == 1
    assert reviews[0]["task_id"] == task["id"]
    assert reviews[0]["status"] == "review"
    quality = client.get("/api/dashboards/ci-quality").json()
    assert quality["test_pass_rate"] == 100
    assert quality["runs"][0]["command"] == "pytest"


def test_worker_blocks_review_when_sandbox_validation_fails(client, monkeypatch):
    task = client.post("/api/tasks", json={"title": "Add vendor gateway contract"}).json()
    monkeypatch.setattr(
        "worker.task_runner.execute",
        lambda *args, **kwargs: {
            "status": "failed",
            "exit_code": 1,
            "stdout": "",
            "stderr": "Tests failed.",
            "duration_seconds": 1,
        },
    )

    from worker.task_runner import process_one

    assert process_one()
    completed = client.get(f"/api/tasks/{task['id']}").json()
    assert completed["status"] == "failed"
    assert completed["outputs"]["tests"]["status"] == "failed"
    assert client.get("/api/reviews").json() == []
    assert client.get("/api/dashboards/ci-quality").json()["test_pass_rate"] == 0


def test_production_worker_leaves_task_queued_without_railway_token(client, monkeypatch):
    task = client.post("/api/tasks", json={"title": "Add lease renewal reminder"}).json()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SANDBOX_MODE", raising=False)
    monkeypatch.delenv("RAILWAY_PROJECT_TOKEN", raising=False)

    from worker.task_runner import process_one

    assert not process_one()
    assert client.get(f"/api/tasks/{task['id']}").json()["status"] == "queued"

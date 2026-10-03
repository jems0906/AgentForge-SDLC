def test_worker_processes_task_through_review(client):
    task = client.post("/api/tasks", json={"title": "Add lease renewal reminder"}).json()

    from worker.task_runner import process_one

    assert process_one()
    completed = client.get(f"/api/tasks/{task['id']}").json()
    assert completed["status"] == "in_review"
    assert completed["outputs"]["tests"]["status"] == "passed"
    reviews = client.get("/api/reviews").json()
    assert len(reviews) == 1
    assert reviews[0]["task_id"] == task["id"]
    assert reviews[0]["status"] == "review"
    quality = client.get("/api/dashboards/ci-quality").json()
    assert quality["test_pass_rate"] == 100
    assert quality["runs"][0]["command"] == "pytest"

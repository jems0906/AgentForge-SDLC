from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_property_management_api_workflow():
    property_response = client.post("/properties", json={"name": "Harbor House", "address": "8 Harbor Road", "unit_count": 12})
    assert property_response.status_code == 201
    property_id = property_response.json()["id"]

    tenant_response = client.post("/tenants", json={"property_id": property_id, "name": "Morgan Lee", "email": "morgan@example.com"})
    assert tenant_response.status_code == 201

    lease_response = client.post("/leases", json={"tenant_id": tenant_response.json()["id"], "starts_on": "2026-01-01", "ends_on": "2026-11-15", "monthly_rent": 1800})
    assert lease_response.status_code == 201
    assert client.get(f"/leases/{lease_response.json()['id']}/renewal-due?today=2026-10-01").json()["due"]

    ticket = client.post("/maintenance", json={"property_id": property_id, "title": "Boiler inspection", "priority": " URGENT "})
    assert ticket.status_code == 201
    assert ticket.json()["priority"] == "urgent"

    payment = client.post("/payments", json={"lease_id": lease_response.json()["id"], "amount": 1800})
    assert payment.status_code == 201
    assert payment.json()["status"] == "validated"


def test_maintenance_rejects_unknown_priority():
    response = client.post("/maintenance", json={"property_id": 1, "title": "Inspect heater", "priority": "whenever"})
    assert response.status_code == 422

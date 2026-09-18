from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_dashboard_detects_seeded_conditions():
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["completed"] == 3
    assert dashboard["blocked"] == 1
    assert dashboard["stale"] == 1
    assert dashboard["open_reviews"] == 3


def test_approval_includes_update_in_report():
    client.post("/api/updates/reset")
    client.post("/api/updates/alex.tan/approve")
    report = client.get("/api/reports/monthly").json()
    assert report["approved_updates"] == 1
    assert any("EXP-102" in item for item in report["achievements"])


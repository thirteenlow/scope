from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def headers(user="bryan"):
    return {"X-User-Id": user}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_developer_sees_only_self_and_cannot_edit_other_user():
    updates = client.get("/api/updates", headers=headers()).json()
    assert len(updates) == 1
    assert updates[0]["developer"]["id"] == "bryan"
    denied = client.post("/api/updates/yam.nee/items", headers=headers(), json={"title": "Not allowed", "detail": "", "category": "blocker"})
    assert denied.status_code == 403


def test_pm_sees_and_can_edit_every_developer():
    updates = client.get("/api/updates", headers=headers("weifa")).json()
    assert len(updates) == 7
    created = client.post("/api/updates/yam.nee/items", headers=headers("weifa"), json={"title": "PM-created follow-up", "detail": "Review during meeting", "category": "in_progress"})
    assert created.status_code == 200


def test_commit_suggestions_include_evidence_links():
    update = client.get("/api/updates", headers=headers()).json()[0]
    assert update["suggestions"]
    evidence = update["suggestions"][0]["evidence"]
    assert any(item["source"] == "git" and item["url"] for item in evidence)


def test_only_pm_can_save_meeting_notes():
    denied = client.put("/api/meeting/notes", headers=headers(), json={"text": "Decision"})
    assert denied.status_code == 403
    allowed = client.put("/api/meeting/notes", headers=headers("weifa"), json={"text": "Decision"})
    assert allowed.status_code == 200


def test_simulated_jira_issue_page_is_rendered():
    response = client.get("/mock/jira/browse/OPS-261")
    assert response.status_code == 200
    assert "Jira Software" in response.text
    assert "SIMULATED" in response.text
    assert "Yam Nee" in response.text


def test_simulated_github_commit_page_contains_diff():
    response = client.get("/mock/git/commit/c8f42ad")
    assert response.status_code == 200
    assert "Pull requests" in response.text
    assert "SIMULATED" in response.text
    assert "src/services/claims.py" in response.text

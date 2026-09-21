from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["product"] == "scope"


def test_bootstrap_contains_mock_integrations():
    data = client.get("/api/bootstrap").json()
    assert data["repository"]["name"] == "acme/expenseflow"
    assert any(issue["key"] == "EXP-241" for issue in data["jira"])
    assert any(member["name"] == "Weifa" and member["role"] == "Product manager" for member in data["team"])


def test_repository_tree_and_file():
    tree = client.get("/api/repo/tree")
    assert tree.status_code == 200
    file = client.get("/api/repo/file", params={"path": "services/expense-api/app/routes/expenses.py"})
    assert file.status_code == 200
    assert "submitted expenses are immutable" in file.json()["content"]


def test_feature_flow_to_jira():
    analysis = client.post("/api/features/FEAT-104/analyze")
    assert analysis.status_code == 200
    assert analysis.json()["risk"] == "high"
    blocked = client.post("/api/features/FEAT-104/sync-jira")
    assert blocked.status_code == 409
    approval = client.post("/api/features/FEAT-104/approve", json={"option_id": "mvp"})
    assert approval.status_code == 200
    synced = client.post("/api/features/FEAT-104/sync-jira")
    assert synced.status_code == 200
    assert len(synced.json()) >= 5
    assert synced.json()[0]["type"] == "Epic"


def test_feature_brief_can_be_updated_before_analysis():
    payload = {"title": "Editable submitted expenses", "description": "Let employees correct submitted claims safely after submission.", "target_weeks": 6}
    updated = client.put("/api/features/FEAT-104", json=payload)
    assert updated.status_code == 200
    assert updated.json()["target_weeks"] == 6


def test_path_traversal_is_blocked():
    response = client.get("/api/repo/file", params={"path": "../../README.md"})
    assert response.status_code == 404


def test_llm_status_reports_provider(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.get("/api/llm/status")
    assert response.status_code == 200
    assert response.json()["provider"] == "Anthropic"
    assert response.json()["configured"] is False


def test_chat_requires_server_side_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "Add receipt OCR"}], "mode": "chat", "target_weeks": 4})
    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]

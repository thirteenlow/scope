from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .analysis import build_dashboard, build_meeting_report, build_updates
from .repository import get_commits, get_developers, get_issues, get_pull_requests


app = FastAPI(title="Sync API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

approved_updates: set[str] = set()


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/developers")
def developers():
    return get_developers()


@app.get("/api/issues")
def issues():
    return get_issues()


@app.get("/api/activity")
def activity():
    return {
        "commits": get_commits(),
        "pull_requests": get_pull_requests(),
    }


@app.get("/api/dashboard")
def dashboard():
    return build_dashboard()


@app.get("/api/updates")
def updates():
    return build_updates(approved_updates)


@app.post("/api/updates/{developer_id}/approve")
def approve_update(developer_id: str):
    developer_ids = {developer.id for developer in get_developers()}
    if developer_id not in developer_ids:
        raise HTTPException(status_code=404, detail="Developer not found")
    approved_updates.add(developer_id)
    return {"developer_id": developer_id, "approved": True}


@app.post("/api/updates/reset")
def reset_updates():
    approved_updates.clear()
    return {"approved": []}


@app.get("/api/reports/monthly")
def monthly_report():
    return build_meeting_report(approved_updates)


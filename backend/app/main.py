from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .llm import LlmConfigurationError, LlmResponseError, is_configured, model_name, talk_to_claude
from .models import ApprovalRequest, ChatRequest, ChatResponse, FeatureCreate, LlmStatus
from .repository import build_tree, read_file, repository_summary
from .state import state


app = FastAPI(title="Scope API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"http://(10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+):5173",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "product": "scope"}


@app.get("/api/llm/status", response_model=LlmStatus)
def llm_status():
    return LlmStatus(configured=is_configured(), model=model_name())


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    try:
        message, analysis, model = await talk_to_claude(payload.messages, payload.mode, payload.target_weeks)
    except LlmConfigurationError as exc:
        raise HTTPException(503, str(exc)) from exc
    except LlmResponseError as exc:
        raise HTTPException(502, str(exc)) from exc
    if analysis:
        state.analyses[analysis.feature_id] = analysis
        feature = state.features[analysis.feature_id]
        latest_request = next((item.content for item in reversed(payload.messages) if item.role == "user"), feature.description)
        state.features[analysis.feature_id] = feature.model_copy(update={"description": latest_request, "target_weeks": payload.target_weeks, "status": "analyzed", "selected_option": None})
    return ChatResponse(message=message, model=model, analysis=analysis, feature_id=analysis.feature_id if analysis else None)


@app.get("/api/bootstrap")
def bootstrap() -> dict:
    return {
        "repository": repository_summary(),
        "features": list(state.features.values()),
        "jira": list(state.jira.values()),
        "team": [
            {"name": "Weifa", "role": "Product manager", "initials": "W"},
            {"name": "Bryan", "role": "Engineering lead", "initials": "B"},
            {"name": "Ng Jin", "role": "Frontend", "initials": "NJ"},
            {"name": "Yi San", "role": "Product engineer", "initials": "YS"},
            {"name": "Roland", "role": "Backend", "initials": "R"},
            {"name": "Dickson", "role": "Platform", "initials": "D"},
            {"name": "Cynthia", "role": "QA", "initials": "C"},
            {"name": "Yam Nee", "role": "Design", "initials": "YN"},
        ],
    }


@app.get("/api/features")
def features() -> list:
    return list(state.features.values())


@app.post("/api/features", status_code=201)
def create_feature(payload: FeatureCreate):
    return state.create_feature(payload)


@app.put("/api/features/{feature_id}")
def update_feature(feature_id: str, payload: FeatureCreate):
    if feature_id not in state.features:
        raise HTTPException(404, "Feature not found")
    return state.update_feature(feature_id, payload)


@app.post("/api/features/{feature_id}/analyze")
def analyze(feature_id: str):
    if feature_id not in state.features:
        raise HTTPException(404, "Feature not found")
    return state.analyze(feature_id)


@app.get("/api/features/{feature_id}/analysis")
def get_analysis(feature_id: str):
    if feature_id not in state.analyses:
        raise HTTPException(404, "Analysis not found")
    return state.analyses[feature_id]


@app.post("/api/features/{feature_id}/approve")
def approve(feature_id: str, payload: ApprovalRequest):
    if feature_id not in state.features or feature_id not in state.analyses:
        raise HTTPException(404, "Analyze the feature first")
    if payload.option_id not in {option.id for option in state.analyses[feature_id].options}:
        raise HTTPException(400, "Unknown scope option")
    return state.approve(feature_id, payload.option_id)


@app.post("/api/features/{feature_id}/sync-jira")
def sync_jira(feature_id: str):
    feature = state.features.get(feature_id)
    if not feature:
        raise HTTPException(404, "Feature not found")
    if feature.status not in {"approved", "synced"}:
        raise HTTPException(409, "Approve a scope option before syncing")
    if feature.status == "synced":
        return [issue for issue in state.jira.values() if "scope-generated" in issue.labels]
    return state.sync_to_jira(feature_id)


@app.get("/api/repo/tree")
def repo_tree():
    return build_tree()


@app.get("/api/repo/file")
def repo_file(path: str = Query(min_length=1)):
    try:
        return read_file(path)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(404, "File not found") from exc


@app.get("/api/jira/issues")
def jira_issues():
    return list(state.jira.values())


@app.get("/api/jira/issues/{key}")
def jira_issue(key: str):
    if key not in state.jira:
        raise HTTPException(404, "Issue not found")
    return state.jira[key]

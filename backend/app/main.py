from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .database import (
    delete_conversation,
    get_conversation,
    list_conversations,
    save_exchange,
    save_jira_sync,
    save_prd,
    select_plan_option,
)
from .llm import (
    LlmConfigurationError,
    LlmResponseError,
    generate_prd,
    is_configured,
    model_name,
    talk_to_claude,
)
from .models import (
    AnalysisResult,
    ApprovalRequest,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    FeatureCreate,
    LlmStatus,
)
from .product_features import PRODUCT_FEATURES
from .repository import (
    build_tree,
    read_file,
    repository_summary,
)
from .state import state


app = FastAPI(
    title="Scope API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=(
        r"http://"
        r"(10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)"
        r":5173"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "product": "scope",
    }


@app.get(
    "/api/llm/status",
    response_model=LlmStatus,
)
def llm_status():
    return LlmStatus(
        configured=is_configured(),
        model=model_name(),
    )


@app.post(
    "/api/chat",
    response_model=ChatResponse,
)
async def chat(payload: ChatRequest):
    try:
        message, analysis, model = await talk_to_claude(
            payload.messages,
            payload.mode,
            payload.target_weeks,
        )
    except LlmConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except LlmResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    if analysis:
        state.analyses[analysis.feature_id] = analysis

        feature = state.features[analysis.feature_id]

        latest_request = next(
            (
                item.content
                for item in reversed(payload.messages)
                if item.role == "user"
            ),
            feature.description,
        )

        state.features[analysis.feature_id] = feature.model_copy(
            update={
                "description": latest_request,
                "target_weeks": payload.target_weeks,
                "status": "analyzed",
                "selected_option": None,
            }
        )

    conversation_id = save_exchange(
        payload.conversation_id,
        payload.messages,
        message,
        payload.target_weeks,
        analysis,
    )

    return ChatResponse(
        message=message,
        model=model,
        analysis=analysis,
        feature_id=(
            analysis.feature_id
            if analysis
            else None
        ),
        conversation_id=conversation_id,
    )


@app.get("/api/conversations")
def conversations():
    return list_conversations()


@app.get("/api/conversations/{conversation_id}")
def conversation(conversation_id: str):
    result = get_conversation(conversation_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return result


@app.delete(
    "/api/conversations/{conversation_id}",
    status_code=204,
)
def remove_conversation(conversation_id: str):
    if not delete_conversation(conversation_id):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )


@app.put(
    "/api/conversations/{conversation_id}/selected-option"
)
def update_selected_option(
    conversation_id: str,
    payload: ApprovalRequest,
):
    conversation_record = get_conversation(conversation_id)

    if not conversation_record:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    analysis = conversation_record.get("analysis")

    if (
        not analysis
        or payload.option_id
        not in {
            option["id"]
            for option in analysis["options"]
        }
    ):
        raise HTTPException(
            status_code=400,
            detail="Unknown scope option",
        )

    select_plan_option(
        conversation_id,
        payload.option_id,
    )

    return {
        "conversation_id": conversation_id,
        "selected_option": payload.option_id,
    }


@app.post(
    "/api/conversations/{conversation_id}/generate-prd"
)
async def generate_conversation_prd(
    conversation_id: str,
    payload: ApprovalRequest,
):
    conversation_record = get_conversation(conversation_id)

    if (
        not conversation_record
        or not conversation_record.get("analysis")
    ):
        raise HTTPException(
            status_code=404,
            detail="Generate a scope plan first",
        )

    analysis = AnalysisResult.model_validate(
        conversation_record["analysis"]
    )

    selected = next(
        (
            option
            for option in analysis.options
            if option.id == payload.option_id
        ),
        None,
    )

    if not selected:
        raise HTTPException(
            status_code=400,
            detail="Unknown scope option",
        )

    messages = [
        ChatMessage(
            role=item["role"],
            content=item["content"],
        )
        for item in conversation_record["messages"]
    ]

    try:
        markdown, model = await generate_prd(
            messages=messages,
            analysis=analysis,
            selected_option=selected,
            target_weeks=conversation_record[
                "target_weeks"
            ],
        )
    except LlmConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except LlmResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    select_plan_option(
        conversation_id,
        payload.option_id,
    )

    save_prd(
        conversation_id,
        markdown,
        model,
    )

    return {
        "markdown": markdown,
        "model": model,
        "selected_option": payload.option_id,
    }


@app.post(
    "/api/conversations/{conversation_id}/sync-jira"
)
def sync_conversation_to_jira(
    conversation_id: str,
    payload: ApprovalRequest,
):
    conversation_record = get_conversation(conversation_id)

    if (
        not conversation_record
        or not conversation_record.get("analysis")
    ):
        raise HTTPException(
            status_code=404,
            detail="Generated plan not found",
        )

    analysis = AnalysisResult.model_validate(
        conversation_record["analysis"]
    )

    valid_option_ids = {
        option.id
        for option in analysis.options
    }

    if payload.option_id not in valid_option_ids:
        raise HTTPException(
            status_code=400,
            detail="Unknown scope option",
        )

    # The same approved scope was already added to Jira.
    # Return any issues that are still available in the mock Jira
    # state rather than creating duplicates.
    if (
        conversation_record.get("jira_synced_at")
        and conversation_record.get("selected_option")
        == payload.option_id
    ):
        return [
            state.jira[key]
            for key in conversation_record.get(
                "jira_issue_keys",
                [],
            )
            if key in state.jira
        ]

    state.analyses[analysis.feature_id] = analysis

    if analysis.feature_id not in state.features:
        raise HTTPException(
            status_code=409,
            detail=(
                "The feature context is no longer available"
            ),
        )

    state.approve(
        analysis.feature_id,
        payload.option_id,
    )

    # Save the option before recording the Jira sync.
    select_plan_option(
        conversation_id,
        payload.option_id,
    )

    created = state.sync_to_jira(
        analysis.feature_id
    )

    save_jira_sync(
        conversation_id,
        [issue.key for issue in created],
    )

    return created


@app.get("/api/product-features")
def product_features():
    return PRODUCT_FEATURES


@app.get("/api/bootstrap")
def bootstrap() -> dict:
    return {
        "repository": repository_summary(),
        "features": list(state.features.values()),
        "jira": list(state.jira.values()),
        "team": [
            {
                "name": "Person",
                "role": "Product manager",
                "initials": "W",
            },
            {
                "name": "Bryan",
                "role": "Engineering lead",
                "initials": "B",
            },
            {
                "name": "Ng Jin",
                "role": "Frontend",
                "initials": "NJ",
            },
            {
                "name": "Yi San",
                "role": "Product engineer",
                "initials": "YS",
            },
            {
                "name": "Roland",
                "role": "Backend",
                "initials": "R",
            },
            {
                "name": "Dickson",
                "role": "Platform",
                "initials": "D",
            },
            {
                "name": "Cynthia",
                "role": "QA",
                "initials": "C",
            },
            {
                "name": "Yam Nee",
                "role": "Design",
                "initials": "YN",
            },
        ],
    }


@app.get("/api/features")
def features() -> list:
    return list(state.features.values())


@app.post(
    "/api/features",
    status_code=201,
)
def create_feature(payload: FeatureCreate):
    return state.create_feature(payload)


@app.put("/api/features/{feature_id}")
def update_feature(
    feature_id: str,
    payload: FeatureCreate,
):
    if feature_id not in state.features:
        raise HTTPException(
            status_code=404,
            detail="Feature not found",
        )

    return state.update_feature(
        feature_id,
        payload,
    )


@app.post("/api/features/{feature_id}/analyze")
def analyze(feature_id: str):
    if feature_id not in state.features:
        raise HTTPException(
            status_code=404,
            detail="Feature not found",
        )

    return state.analyze(feature_id)


@app.get("/api/features/{feature_id}/analysis")
def get_analysis(feature_id: str):
    if feature_id not in state.analyses:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    return state.analyses[feature_id]


@app.post("/api/features/{feature_id}/approve")
def approve(
    feature_id: str,
    payload: ApprovalRequest,
):
    if (
        feature_id not in state.features
        or feature_id not in state.analyses
    ):
        raise HTTPException(
            status_code=404,
            detail="Analyze the feature first",
        )

    valid_option_ids = {
        option.id
        for option in state.analyses[
            feature_id
        ].options
    }

    if payload.option_id not in valid_option_ids:
        raise HTTPException(
            status_code=400,
            detail="Unknown scope option",
        )

    return state.approve(
        feature_id,
        payload.option_id,
    )


@app.post("/api/features/{feature_id}/sync-jira")
def sync_jira(feature_id: str):
    feature = state.features.get(feature_id)

    if not feature:
        raise HTTPException(
            status_code=404,
            detail="Feature not found",
        )

    if feature.status not in {
        "approved",
        "synced",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Approve a scope option before syncing"
            ),
        )

    if feature.status == "synced":
        return [
            issue
            for issue in state.jira.values()
            if "scope-generated" in issue.labels
        ]

    return state.sync_to_jira(feature_id)


@app.get("/api/repo/tree")
def repo_tree():
    return build_tree()


@app.get("/api/repo/file")
def repo_file(
    path: str = Query(min_length=1),
):
    try:
        return read_file(path)
    except (
        FileNotFoundError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        ) from exc


@app.get("/api/jira/issues")
def jira_issues():
    return list(state.jira.values())


@app.get("/api/jira/issues/{key}")
def jira_issue(key: str):
    if key not in state.jira:
        raise HTTPException(
            status_code=404,
            detail="Issue not found",
        )

    return state.jira[key]
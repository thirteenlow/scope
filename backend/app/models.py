from typing import Literal

from pydantic import BaseModel, Field


class FeatureCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=2000)
    target_weeks: int = Field(ge=1, le=52)


class FeatureRequest(FeatureCreate):
    id: str
    owner: str
    status: Literal["draft", "analyzed", "approved", "synced"]
    created_at: str
    selected_option: str | None = None


class Evidence(BaseModel):
    id: str
    type: Literal["verified", "inferred", "question"]
    title: str
    detail: str
    path: str | None = None
    line: int | None = None
    confidence: int


class ScopeOption(BaseModel):
    id: str
    name: str
    duration: str
    confidence: Literal["high", "medium", "low"]
    summary: str
    includes: list[str]
    excludes: list[str]
    recommended: bool = False


class PlanItem(BaseModel):
    temp_key: str
    type: Literal["Epic", "Story", "Task", "Spike"]
    title: str
    description: str
    parent: str | None = None
    estimate: int | None = None
    discipline: str | None = None
    evidence_ids: list[str] = []


class AnalysisResult(BaseModel):
    feature_id: str
    verdict: str
    feasibility: int
    timeline_confidence: int
    risk: Literal["low", "medium", "high"]
    summary: str
    affected_areas: list[str]
    evidence: list[Evidence]
    options: list[ScopeOption]
    plan: list[PlanItem]
    questions: list[str]


class ApprovalRequest(BaseModel):
    option_id: str


class JiraIssue(BaseModel):
    key: str
    type: Literal["Epic", "Story", "Task", "Spike"]
    summary: str
    description: str
    status: str
    parent: str | None = None
    estimate: int | None = None
    assignee: str | None = None
    labels: list[str] = []
    evidence_paths: list[str] = []


class RepoNode(BaseModel):
    name: str
    path: str
    type: Literal["file", "folder"]
    children: list["RepoNode"] | None = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    mode: Literal["chat", "plan"] = "chat"
    target_weeks: int = Field(default=4, ge=1, le=52)


class ChatResponse(BaseModel):
    message: str
    model: str
    analysis: AnalysisResult | None = None
    feature_id: str | None = None


class LlmStatus(BaseModel):
    configured: bool
    provider: str = "Anthropic"
    model: str

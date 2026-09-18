from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["developer", "pm"]
Category = Literal["completed", "in_progress", "blocker"]


class User(BaseModel):
    id: str
    name: str
    role: Role
    title: str
    avatar: str


class Issue(BaseModel):
    key: str
    summary: str
    status: Literal["To Do", "In Progress", "Blocked", "Done"]
    assignee: str
    updated_at: str
    due_date: str | None = None
    blocked_reason: str | None = None
    planned: bool = True


class PullRequest(BaseModel):
    number: int
    title: str
    author: str
    status: Literal["open", "merged"]
    created_at: str
    linked_issue: str
    approvals: int = 0


class Commit(BaseModel):
    sha: str
    message: str
    author: str
    committed_at: str
    issue_key: str


class Evidence(BaseModel):
    source: Literal["jira", "git", "manual"]
    label: str
    reference: str
    url: str | None = None


class Suggestion(BaseModel):
    id: str
    developer_id: str
    title: str
    detail: str
    category: Category
    occurred_at: str
    evidence: list[Evidence]


class UpdateItem(BaseModel):
    id: str
    developer_id: str
    title: str
    detail: str = ""
    category: Category
    target_date: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    source: Literal["suggested", "manual"] = "manual"


class UpdateItemCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    detail: str = Field(default="", max_length=1000)
    category: Category
    target_date: str | None = None


class UpdateItemPatch(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    detail: str | None = Field(default=None, max_length=1000)
    category: Category | None = None
    target_date: str | None = None


class AcceptSuggestion(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    detail: str | None = Field(default=None, max_length=1000)
    category: Category | None = None


class DeveloperUpdate(BaseModel):
    developer: User
    items: list[UpdateItem]
    suggestions: list[Suggestion]
    approved: bool = False


class Dashboard(BaseModel):
    month: str
    meeting_date: str
    completed: int
    active: int
    blocked: int
    stale: int
    open_reviews: int
    planned_percent: int
    issues: list[Issue]


class CalendarEvent(BaseModel):
    id: str
    date: str
    title: str
    kind: Literal["meeting", "cutoff", "issue", "review"]
    owner: str | None = None


class Insight(BaseModel):
    id: str
    severity: Literal["info", "warning", "positive"]
    title: str
    detail: str
    evidence: list[str]


class MeetingNote(BaseModel):
    text: str = Field(max_length=5000)


class MeetingAction(BaseModel):
    id: str
    action: Literal["create_issue", "carry_over"]
    title: str
    issue_key: str | None = None
    owner: str | None = None
    approved: bool = False


class MeetingWorkspace(BaseModel):
    month: str
    meeting_date: str
    notes: str
    actions: list[MeetingAction]
    approved_updates: int
    total_updates: int

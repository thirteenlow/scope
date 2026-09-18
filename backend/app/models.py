from typing import Literal

from pydantic import BaseModel, Field


class Developer(BaseModel):
    id: str
    name: str
    role: str


class Issue(BaseModel):
    key: str
    summary: str
    status: Literal["To Do", "In Progress", "Blocked", "Done"]
    assignee: str
    updated_at: str
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
    label: str
    reference: str


class WorkItem(BaseModel):
    issue_key: str
    summary: str
    evidence: list[Evidence] = Field(default_factory=list)


class DeveloperUpdate(BaseModel):
    developer_id: str
    developer_name: str
    completed: list[WorkItem]
    in_progress: list[WorkItem]
    blockers: list[WorkItem]
    needs_attention: list[WorkItem]
    approved: bool = False


class Dashboard(BaseModel):
    month: str
    completed: int
    active: int
    blocked: int
    stale: int
    open_reviews: int
    issues: list[Issue]


class MeetingReport(BaseModel):
    month: str
    achievements: list[str]
    blockers: list[str]
    decisions_needed: list[str]
    approved_updates: int


from datetime import date, datetime
from uuid import uuid4

from .models import Evidence, MeetingAction, Suggestion, UpdateItem
from .repository import get_commits, get_issues

MEETING_DATE = date(2026, 8, 31)
CYCLE_START = date(2026, 8, 1)


def _commit_suggestions() -> list[Suggestion]:
    issues = {issue.key: issue for issue in get_issues()}
    result: list[Suggestion] = []
    for commit in get_commits():
        committed = datetime.fromisoformat(commit.committed_at).date()
        if not CYCLE_START <= committed <= MEETING_DATE:
            continue
        issue = issues.get(commit.issue_key)
        evidence = [Evidence(source="git", label=commit.sha, reference=f"commit:{commit.sha}", url=f"/mock/git/commit/{commit.sha}")]
        if issue:
            evidence.append(Evidence(source="jira", label=issue.key, reference=f"jira:{issue.key}", url=f"/mock/jira/browse/{issue.key}"))
        result.append(Suggestion(
            id=f"suggestion-{commit.sha}", developer_id=commit.author,
            title=issue.summary if issue else commit.message,
            detail=f"Suggested from commit: {commit.message}",
            category="completed" if issue and issue.status == "Done" else "in_progress",
            occurred_at=commit.committed_at, evidence=evidence,
        ))
    return result


suggestions = _commit_suggestions()
update_items: list[UpdateItem] = [UpdateItem(
    id="manual-blocker-yam-nee", developer_id="yam.nee",
    title="Camera permission guidance pending",
    detail="Waiting for platform guidance before finalising receipt capture.",
    category="blocker", target_date="2026-08-31",
    evidence=[Evidence(source="jira", label="OPS-261", reference="jira:OPS-261", url="/mock/jira/browse/OPS-261")],
    source="manual",
)]
approved_updates: set[str] = set()
dismissed_suggestions: set[str] = set()
meeting_notes = ""
meeting_actions: list[MeetingAction] = []
dynamic_issues = get_issues()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"

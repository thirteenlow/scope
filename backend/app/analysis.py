from datetime import date, datetime

from .models import (
    Dashboard,
    DeveloperUpdate,
    Evidence,
    MeetingReport,
    WorkItem,
)
from .repository import get_commits, get_developers, get_issues, get_pull_requests


REPORT_DATE = date(2026, 8, 31)
STALE_AFTER_DAYS = 7


def _days_since(value: str) -> int:
    updated = datetime.fromisoformat(value).date()
    return (REPORT_DATE - updated).days


def _issue_item(issue, extra_evidence: list[Evidence] | None = None) -> WorkItem:
    evidence = [Evidence(label=issue.key, reference=f"jira:{issue.key}")]
    evidence.extend(extra_evidence or [])
    return WorkItem(
        issue_key=issue.key,
        summary=issue.summary,
        evidence=evidence,
    )


def build_dashboard() -> Dashboard:
    issues = get_issues()
    pull_requests = get_pull_requests()
    return Dashboard(
        month="August 2026",
        completed=sum(issue.status == "Done" for issue in issues),
        active=sum(issue.status == "In Progress" for issue in issues),
        blocked=sum(issue.status == "Blocked" for issue in issues),
        stale=sum(
            issue.status == "In Progress"
            and _days_since(issue.updated_at) > STALE_AFTER_DAYS
            for issue in issues
        ),
        open_reviews=sum(pr.status == "open" for pr in pull_requests),
        issues=issues,
    )


def build_updates(approved_ids: set[str]) -> list[DeveloperUpdate]:
    issues = get_issues()
    commits = get_commits()
    pull_requests = get_pull_requests()
    updates: list[DeveloperUpdate] = []

    for developer in get_developers():
        assigned = [issue for issue in issues if issue.assignee == developer.id]
        completed = []
        in_progress = []
        blockers = []
        needs_attention = []

        for issue in assigned:
            commit_evidence = [
                Evidence(label=commit.sha, reference=f"commit:{commit.sha}")
                for commit in commits
                if commit.issue_key == issue.key
            ]
            item = _issue_item(issue, commit_evidence)

            if issue.status == "Done":
                completed.append(item)
            elif issue.status == "Blocked":
                blockers.append(item)
            elif issue.status == "In Progress":
                in_progress.append(item)
                if _days_since(issue.updated_at) > STALE_AFTER_DAYS:
                    needs_attention.append(item)

            delayed_reviews = [
                pr
                for pr in pull_requests
                if pr.linked_issue == issue.key
                and pr.status == "open"
                and pr.approvals == 0
            ]
            if delayed_reviews and all(
                existing.issue_key != issue.key for existing in needs_attention
            ):
                needs_attention.append(
                    _issue_item(
                        issue,
                        [
                            Evidence(
                                label=f"PR #{pr.number}",
                                reference=f"pull-request:{pr.number}",
                            )
                            for pr in delayed_reviews
                        ],
                    )
                )

        updates.append(
            DeveloperUpdate(
                developer_id=developer.id,
                developer_name=developer.name,
                completed=completed,
                in_progress=in_progress,
                blockers=blockers,
                needs_attention=needs_attention,
                approved=developer.id in approved_ids,
            )
        )

    return updates


def build_meeting_report(approved_ids: set[str]) -> MeetingReport:
    updates = [update for update in build_updates(approved_ids) if update.approved]
    return MeetingReport(
        month="August 2026",
        achievements=[
            f"{item.issue_key}: {item.summary}"
            for update in updates
            for item in update.completed
        ],
        blockers=[
            f"{item.issue_key}: {item.summary}"
            for update in updates
            for item in update.blockers
        ],
        decisions_needed=[
            f"Review {item.issue_key}: {item.summary}"
            for update in updates
            for item in update.needs_attention
        ],
        approved_updates=len(updates),
    )


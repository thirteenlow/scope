from datetime import date, datetime

from . import state
from .models import CalendarEvent, Dashboard, DeveloperUpdate, Insight
from .repository import get_pull_requests, get_users

REPORT_DATE = date(2026, 8, 31)


def _days_since(value: str) -> int:
    return (REPORT_DATE - datetime.fromisoformat(value).date()).days


def build_dashboard() -> Dashboard:
    issues = state.dynamic_issues
    pull_requests = get_pull_requests()
    completed = sum(issue.status == "Done" for issue in issues)
    return Dashboard(
        month="August 2026", meeting_date=state.MEETING_DATE.isoformat(),
        completed=completed,
        active=sum(issue.status == "In Progress" for issue in issues),
        blocked=sum(issue.status == "Blocked" for issue in issues),
        stale=sum(issue.status == "In Progress" and _days_since(issue.updated_at) > 7 for issue in issues),
        open_reviews=sum(pr.status == "open" for pr in pull_requests),
        planned_percent=round(100 * sum(issue.planned and issue.status == "Done" for issue in issues) / max(completed, 1)),
        issues=issues,
    )


def build_updates(viewer_id: str, is_pm: bool) -> list[DeveloperUpdate]:
    developers = [user for user in get_users() if user.role == "developer"]
    if not is_pm:
        developers = [user for user in developers if user.id == viewer_id]
    return [DeveloperUpdate(
        developer=developer,
        items=[item for item in state.update_items if item.developer_id == developer.id],
        suggestions=[item for item in state.suggestions if item.developer_id == developer.id and item.id not in state.dismissed_suggestions],
        approved=developer.id in state.approved_updates,
    ) for developer in developers]


def build_calendar() -> list[CalendarEvent]:
    events = [
        CalendarEvent(id="cycle-start", date="2026-08-01", title="Update cycle opens", kind="cutoff"),
        CalendarEvent(id="review-cutoff", date="2026-08-28", title="Developer review cutoff", kind="cutoff"),
        CalendarEvent(id="monthly-meeting", date="2026-08-31", title="Monthly development sync", kind="meeting"),
    ]
    events.extend(CalendarEvent(
        id=f"issue-{issue.key}", date=issue.due_date, title=f"{issue.key} · {issue.summary}",
        kind="issue", owner=issue.assignee,
    ) for issue in state.dynamic_issues if issue.due_date)
    return sorted(events, key=lambda event: event.date)


def build_insights() -> list[Insight]:
    dashboard = build_dashboard()
    result: list[Insight] = []
    if dashboard.blocked:
        result.append(Insight(
            id="blocked-work", severity="warning", title="Blocker needs a meeting decision",
            detail="Resolve ownership or dependency during the monthly sync.",
            evidence=[issue.key for issue in dashboard.issues if issue.status == "Blocked"],
        ))
    if dashboard.open_reviews >= 2:
        result.append(Insight(
            id="review-queue", severity="warning", title="Review queue is building",
            detail=f"{dashboard.open_reviews} pull requests remain open at cycle end.",
            evidence=[f"PR #{pr.number}" for pr in get_pull_requests() if pr.status == "open"],
        ))
    result.append(Insight(
        id="plan-stability", severity="positive" if dashboard.planned_percent >= 70 else "info",
        title="Plan stability", detail=f"{dashboard.planned_percent}% of completed Jira work was planned for this cycle.",
        evidence=[issue.key for issue in dashboard.issues if issue.status == "Done"],
    ))
    return result


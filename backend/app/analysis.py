from .models import AnalysisResult, Evidence, PlanItem, ScopeOption


def analyze_feature(feature_id: str, title: str, description: str, target_weeks: int) -> AnalysisResult:
    text = f"{title} {description}".lower()
    edit_submitted = "edit" in text and ("submitted" in text or "submission" in text)

    if edit_submitted:
        return _submitted_expense_analysis(feature_id, target_weeks)

    evidence = [
        Evidence(id="EV-1", type="verified", title="Expense domain is modular", detail="Expense creation and approval logic live in separate services.", path="services/expense-api/app/routes/expenses.py", line=18, confidence=96),
        Evidence(id="EV-2", type="question", title="Acceptance criteria missing", detail="The brief does not specify mobile behavior or audit requirements.", confidence=100),
    ]
    option = ScopeOption(id="balanced", name="Balanced delivery", duration=f"{max(2, target_weeks)}–{max(3, target_weeks + 1)} weeks", confidence="medium", summary="Deliver the core web flow first and validate wider workflow implications during implementation.", includes=["Web experience", "API changes", "Automated tests", "Audit events"], excludes=["Mobile parity", "Historical migration"], recommended=True)
    plan = _generic_plan(title, evidence)
    return AnalysisResult(feature_id=feature_id, verdict="Feasible after clarification", feasibility=78, timeline_confidence=64, risk="medium", summary="The codebase has clear extension points, but the brief needs sharper workflow rules before engineering commits to the date.", affected_areas=["Web app", "Expense API", "Audit log"], evidence=evidence, options=[option], plan=plan, questions=["Should this be available on mobile at launch?", "Which fields are allowed to change?", "What audit detail is required?"])


def _submitted_expense_analysis(feature_id: str, target_weeks: int) -> AnalysisResult:
    evidence = [
        Evidence(id="EV-1", type="verified", title="Submitted expenses are immutable", detail="The API rejects updates unless an expense is still in DRAFT status.", path="services/expense-api/app/routes/expenses.py", line=31, confidence=99),
        Evidence(id="EV-2", type="verified", title="Approval starts immediately", detail="Submission creates the first approval step synchronously.", path="services/expense-api/app/services/submission.py", line=13, confidence=98),
        Evidence(id="EV-3", type="verified", title="Mobile and web share the API", detail="Both clients call PATCH /expenses/:id, so the rule is enforced centrally.", path="apps/web/src/api/expenses.ts", line=11, confidence=96),
        Evidence(id="EV-4", type="verified", title="Audit trail lacks field-level changes", detail="Current audit events store an action and timestamp but no before/after values.", path="services/expense-api/app/models/audit.py", line=7, confidence=97),
        Evidence(id="EV-5", type="inferred", title="Material edits should restart approval", detail="Changing amount or currency after approval begins could invalidate the approver's decision.", path="docs/expense-workflow.md", line=18, confidence=86),
        Evidence(id="EV-6", type="question", title="Define the edit boundary", detail="The brief does not say whether edits remain allowed after a manager has approved or Finance has begun reimbursement.", confidence=100),
    ]
    options = [
        ScopeOption(id="mvp", name="Guarded edit window", duration="4 weeks", confidence="medium", summary="Meet the target with a controlled web-first edit window before manager approval.", includes=["24-hour edit window", "Description, category and receipt edits", "Block after first approval", "Field-level audit history", "Manager notification", "Web experience"], excludes=["Amount, currency and expense-date edits", "Mobile UI", "Edits after approval"], recommended=True),
        ScopeOption(id="full", name="Full workflow change", duration="8–10 weeks", confidence="medium", summary="Support material edits across clients and safely restart approvals when financial fields change.", includes=["All editable fields", "Web and mobile", "Approval restart rules", "Reimbursement lock", "Full change history", "Notification preferences"], excludes=["Historical expense migration"], recommended=False),
        ScopeOption(id="withdraw", name="Withdraw and resubmit", duration="2–4 weeks", confidence="high", summary="Avoid mutating submitted records: withdraw and duplicate the expense into a new editable draft.", includes=["Withdraw action", "Draft duplication", "Original audit preserved", "Web and mobile API support"], excludes=["Editing the original submission", "Approval continuation"], recommended=False),
    ]
    plan = [
        PlanItem(temp_key="EPIC-1", type="Epic", title="Safe post-submission expense corrections", description="Allow employees to correct non-financial details without weakening approval and audit controls.", estimate=21, evidence_ids=["EV-1", "EV-2", "EV-4"]),
        PlanItem(temp_key="STORY-1", type="Story", title="Edit eligible submitted expenses", description="As an employee, I can correct eligible fields within 24 hours and before manager approval.", parent="EPIC-1", estimate=5, discipline="product", evidence_ids=["EV-1", "EV-6"]),
        PlanItem(temp_key="TASK-1", type="Task", title="Add submitted-expense edit policy", description="Create a domain policy for time, status and field eligibility.", parent="STORY-1", estimate=3, discipline="backend", evidence_ids=["EV-1", "EV-2"]),
        PlanItem(temp_key="TASK-2", type="Task", title="Build correction mode in expense form", description="Reuse the draft form with immutable financial fields and an expiry indicator.", parent="STORY-1", estimate=5, discipline="frontend", evidence_ids=["EV-3"]),
        PlanItem(temp_key="STORY-2", type="Story", title="Preserve a defensible change history", description="As Finance, I can see exactly what changed after submission.", parent="EPIC-1", estimate=5, discipline="platform", evidence_ids=["EV-4"]),
        PlanItem(temp_key="TASK-3", type="Task", title="Store field-level audit events", description="Persist before/after values, actor, reason and request correlation ID.", parent="STORY-2", estimate=3, discipline="backend", evidence_ids=["EV-4"]),
        PlanItem(temp_key="STORY-3", type="Story", title="Keep approvers aware of corrections", description="As a manager, I am notified when a submitted expense changes before my review.", parent="EPIC-1", estimate=3, discipline="workflow", evidence_ids=["EV-2", "EV-5"]),
        PlanItem(temp_key="TASK-4", type="Task", title="Send expense-corrected notification", description="Publish a correction event and update the manager notification template.", parent="STORY-3", estimate=2, discipline="backend", evidence_ids=["EV-2"]),
    ]
    return AnalysisResult(feature_id=feature_id, verdict="Feasible with guarded scope", feasibility=82, timeline_confidence=68 if target_weeks >= 4 else 34, risk="high", summary="The four-week target is plausible only if financial fields, mobile UI and post-approval edits are excluded. The current API deliberately makes submitted expenses immutable, and approval begins immediately.", affected_areas=["Expense API", "Approval service", "Web app", "Audit model", "Notifications"], evidence=evidence, options=options, plan=plan, questions=["Does the 24-hour window end early once a manager approves?", "Must mobile users edit in the first release?", "Should receipt replacement require a reason?", "Who can view field-level history?"])


def _generic_plan(title: str, evidence: list[Evidence]) -> list[PlanItem]:
    return [
        PlanItem(temp_key="EPIC-1", type="Epic", title=title, description="Deliver the approved feature outcome.", estimate=13, evidence_ids=[evidence[0].id]),
        PlanItem(temp_key="STORY-1", type="Story", title="Complete the primary user journey", description="Implement the approved happy path and validation rules.", parent="EPIC-1", estimate=5, evidence_ids=[evidence[0].id]),
        PlanItem(temp_key="TASK-1", type="Task", title="Extend the Expense API", description="Add the required API behavior and automated coverage.", parent="STORY-1", estimate=3, discipline="backend", evidence_ids=[evidence[0].id]),
        PlanItem(temp_key="TASK-2", type="Task", title="Build the web experience", description="Add the interface, loading and error states.", parent="STORY-1", estimate=5, discipline="frontend", evidence_ids=[evidence[0].id]),
    ]


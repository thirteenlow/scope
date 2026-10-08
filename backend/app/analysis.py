from .models import AnalysisResult, Evidence, PlanItem, ScopeOption


def analyze_feature(feature_id: str, title: str, description: str, target_weeks: int) -> AnalysisResult:
    text = f"{title} {description}".lower()
    if "roll" in text or "carry" in text or "leftover" in text:
        return _rollover_analysis(feature_id, target_weeks)

    evidence = [
        Evidence(id="EV-1", type="verified", title="Budget calculations are centralized", detail="Budget API owns category assignments and available balances.", path="services/budget-api/app/services/allocation.py", line=4, confidence=97),
        Evidence(id="EV-2", type="question", title="Behavior needs clarification", detail="The brief does not define mobile support, historical behavior or migration expectations.", confidence=100),
    ]
    option = ScopeOption(id="balanced", name="Web-first release", duration=f"{max(2, target_weeks)}–{max(3, target_weeks + 1)} weeks", confidence="medium", summary="Deliver the core personal budgeting flow on web and validate calculation edge cases before mobile rollout.", includes=["Web experience", "Budget API changes", "Automated calculation tests", "Personal data isolation"], excludes=["Mobile parity", "Historical recalculation"], recommended=True)
    plan = [
        PlanItem(temp_key="EPIC-1", type="Epic", title=title, description="Deliver the approved personal budgeting outcome.", estimate=13, evidence_ids=["EV-1"]),
        PlanItem(temp_key="STORY-1", type="Story", title="Complete the primary budgeting journey", description="Implement the approved happy path and financial validation rules.", parent="EPIC-1", estimate=5, evidence_ids=["EV-1"]),
        PlanItem(temp_key="TASK-1", type="Task", title="Extend Budget API", description="Add the required domain behavior and automated coverage.", parent="STORY-1", estimate=3, discipline="backend", evidence_ids=["EV-1"]),
        PlanItem(temp_key="TASK-2", type="Task", title="Build the web experience", description="Add the interface, loading states and error recovery.", parent="STORY-1", estimate=5, discipline="frontend", evidence_ids=["EV-1"]),
    ]
    return AnalysisResult(feature_id=feature_id, verdict="Feasible after clarification", feasibility=79, timeline_confidence=64, risk="medium", summary="PocketPlan has clear extension points, but financial behavior must be precise before engineering commits to the date.", affected_areas=["Web dashboard", "Budget API", "Calculation engine"], evidence=evidence, options=[option], plan=plan, questions=["Should this work on mobile at launch?", "Should historical months change?", "How should negative balances behave?"])


def _rollover_analysis(feature_id: str, target_weeks: int) -> AnalysisResult:
    evidence = [
        Evidence(id="EV-1", type="verified", title="New months start at zero", detail="Month creation copies categories but resets assigned, activity and available amounts to zero.", path="services/budget-api/app/services/month_close.py", line=10, confidence=99),
        Evidence(id="EV-2", type="verified", title="Months are intentionally independent", detail="ADR-008 requires stable historical months and calls out rollover edge cases.", path="docs/decisions/ADR-008-independent-budget-months.md", line=5, confidence=99),
        Evidence(id="EV-3", type="verified", title="Available balance is derived", detail="Available amount is assigned minus activity and is stored on each monthly category row.", path="services/budget-api/app/services/allocation.py", line=4, confidence=97),
        Evidence(id="EV-4", type="verified", title="Web calculates a duplicate balance", detail="CategoryRow recalculates availability in the client instead of displaying the API value.", path="apps/web/src/features/budget/CategoryRow.tsx", line=4, confidence=96),
        Evidence(id="EV-5", type="inferred", title="Late transactions can change rollover", detail="A transaction imported into a closed month could alter the balance that was previously carried forward.", path="docs/monthly-budget-cycle.md", line=8, confidence=86),
        Evidence(id="EV-6", type="question", title="Negative-balance policy is undefined", detail="The request does not say whether overspending should reduce next month's available money.", confidence=100),
    ]
    options = [
        ScopeOption(id="positive-only", name="Positive balances only", duration="4 weeks", confidence="medium", summary="Carry unused positive category balances forward while leaving overspending in the closed month.", includes=["Per-category rollover toggle", "Positive balance carry-forward", "Rollover audit record", "Web indicators", "Calculation tests"], excludes=["Negative balance rollover", "Historical recalculation", "Mobile settings"], recommended=True),
        ScopeOption(id="full-rollover", name="Full balance rollover", duration="7–9 weeks", confidence="medium", summary="Carry positive and negative balances with explicit policies for late transactions and category changes.", includes=["Positive and negative rollover", "Late-transaction adjustment", "Deleted-category handling", "Web and mobile", "Historical trace"], excludes=["Rewriting months before feature activation"], recommended=False),
        ScopeOption(id="manual-move", name="Manual month-end move", duration="2–3 weeks", confidence="high", summary="Let users review leftovers and choose what to move before closing a month.", includes=["Month-end review", "Select categories", "Manual transfer entries", "Clear audit trail"], excludes=["Automatic rollover", "Negative balance transfer"], recommended=False),
    ]
    plan = [
        PlanItem(temp_key="EPIC-1", type="Epic", title="Carry category money into the next month", description="Help individuals preserve intentional savings in budget categories across month boundaries.", estimate=21, evidence_ids=["EV-1", "EV-2", "EV-3"]),
        PlanItem(temp_key="STORY-1", type="Story", title="Choose which categories roll over", description="As a user, I can enable rollover for categories where I intentionally build a balance.", parent="EPIC-1", estimate=5, discipline="product", evidence_ids=["EV-2", "EV-6"]),
        PlanItem(temp_key="TASK-1", type="Task", title="Store category rollover policy", description="Add a per-user category setting and migration with safe defaults.", parent="STORY-1", estimate=3, discipline="backend", evidence_ids=["EV-2"]),
        PlanItem(temp_key="TASK-2", type="Task", title="Add rollover controls to budget settings", description="Let users enable rollover and explain its month-end behavior.", parent="STORY-1", estimate=3, discipline="frontend", evidence_ids=["EV-4"]),
        PlanItem(temp_key="STORY-2", type="Story", title="Create the next month with carried balances", description="As a user, my eligible unused money remains available when a new month begins.", parent="EPIC-1", estimate=8, discipline="platform", evidence_ids=["EV-1", "EV-3"]),
        PlanItem(temp_key="TASK-3", type="Task", title="Extend month creation calculation", description="Carry positive eligible balances forward without mutating the closed month.", parent="STORY-2", estimate=5, discipline="backend", evidence_ids=["EV-1", "EV-2", "EV-3"]),
        PlanItem(temp_key="TASK-4", type="Task", title="Remove duplicate client calculation", description="Display the API-provided available balance consistently in the budget UI.", parent="STORY-2", estimate=2, discipline="frontend", evidence_ids=["EV-4"]),
        PlanItem(temp_key="STORY-3", type="Story", title="Understand where rollover money came from", description="As a user, I can distinguish new assignments from money carried from last month.", parent="EPIC-1", estimate=5, discipline="product", evidence_ids=["EV-2", "EV-5"]),
        PlanItem(temp_key="TASK-5", type="Task", title="Record and display rollover entries", description="Persist source month, destination month and amount, then show them in category details.", parent="STORY-3", estimate=3, discipline="backend", evidence_ids=["EV-2", "EV-5"]),
    ]
    return AnalysisResult(feature_id=feature_id, verdict="Feasible with a positive-only policy", feasibility=84, timeline_confidence=72 if target_weeks >= 4 else 38, risk="medium", summary="The four-week target is credible if PocketPlan carries only positive balances for opted-in categories and does not recalculate historical months. Full negative-balance and late-transaction handling would expand the work materially.", affected_areas=["Month creation", "Category settings", "Calculation engine", "Budget dashboard", "Database"], evidence=evidence, options=options, plan=plan, questions=["Should overspent categories reduce the next month?", "What happens when a late transaction enters a closed month?", "Should rollover default on or off for new categories?", "Does mobile need the setting at launch?"])

from datetime import UTC, datetime
from uuid import uuid4

from .analysis import analyze_feature
from .models import AnalysisResult, FeatureCreate, FeatureRequest, JiraIssue


class AppState:
    def __init__(self) -> None:
        self.features: dict[str, FeatureRequest] = {}
        self.analyses: dict[str, AnalysisResult] = {}
        self.jira: dict[str, JiraIssue] = {}
        self._seed()

    def _seed(self) -> None:
        feature = FeatureRequest(
            id="FEAT-104",
            title="Editable submitted expenses",
            description="Allow employees to edit an expense for 24 hours after submission. We need this within four weeks.",
            target_weeks=4,
            owner="Weifa",
            status="draft",
            created_at="2026-09-21T09:30:00Z",
        )
        self.features[feature.id] = feature
        seeds = [
            JiraIssue(key="EXP-241", type="Epic", summary="Receipt OCR capture", description="Extract receipt details and let employees verify them.", status="In Progress", estimate=34, assignee="Bryan", labels=["expenseflow", "ai"]),
            JiraIssue(key="EXP-256", type="Story", summary="Show OCR confidence per field", description="Highlight low-confidence values before submission.", status="In Review", parent="EXP-241", estimate=5, assignee="Yi San", labels=["frontend"], evidence_paths=["apps/web/src/features/expenses/ExpenseForm.tsx"]),
            JiraIssue(key="EXP-263", type="Task", summary="Retry failed reimbursement events", description="Add idempotent retries for provider timeouts.", status="To Do", estimate=3, assignee="Roland", labels=["backend"]),
        ]
        self.jira = {issue.key: issue for issue in seeds}

    def create_feature(self, payload: FeatureCreate) -> FeatureRequest:
        identifier = f"FEAT-{105 + len(self.features) - 1}"
        feature = FeatureRequest(id=identifier, owner="Weifa", status="draft", created_at=datetime.now(UTC).isoformat(), **payload.model_dump())
        self.features[identifier] = feature
        return feature

    def update_feature(self, feature_id: str, payload: FeatureCreate) -> FeatureRequest:
        current = self.features[feature_id]
        updated = current.model_copy(update={**payload.model_dump(), "status": "draft", "selected_option": None})
        self.features[feature_id] = updated
        self.analyses.pop(feature_id, None)
        return updated

    def analyze(self, feature_id: str) -> AnalysisResult:
        feature = self.features[feature_id]
        result = analyze_feature(feature.id, feature.title, feature.description, feature.target_weeks)
        self.analyses[feature_id] = result
        self.features[feature_id] = feature.model_copy(update={"status": "analyzed"})
        return result

    def approve(self, feature_id: str, option_id: str) -> FeatureRequest:
        feature = self.features[feature_id]
        self.features[feature_id] = feature.model_copy(update={"status": "approved", "selected_option": option_id})
        return self.features[feature_id]

    def sync_to_jira(self, feature_id: str) -> list[JiraIssue]:
        feature = self.features[feature_id]
        analysis = self.analyses[feature_id]
        mapping: dict[str, str] = {}
        created: list[JiraIssue] = []
        next_number = max([int(key.split("-")[1]) for key in self.jira] + [263]) + 1
        evidence_map = {item.id: item for item in analysis.evidence}
        for item in analysis.plan:
            key = f"EXP-{next_number}"
            next_number += 1
            mapping[item.temp_key] = key
            paths = [evidence_map[evidence_id].path for evidence_id in item.evidence_ids if evidence_id in evidence_map and evidence_map[evidence_id].path]
            issue = JiraIssue(key=key, type=item.type, summary=item.title, description=item.description, status="To Do", parent=mapping.get(item.parent or ""), estimate=item.estimate, assignee=None, labels=["scope-generated", item.discipline or "product"], evidence_paths=paths)
            self.jira[key] = issue
            created.append(issue)
        self.features[feature_id] = feature.model_copy(update={"status": "synced"})
        return created


state = AppState()

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT / "mock-expenseflow"


def _safe_path(relative_path: str) -> Path:
    candidate = (REPO_ROOT / relative_path).resolve()
    if candidate != REPO_ROOT and REPO_ROOT not in candidate.parents:
        raise ValueError("Path is outside the mock repository")
    return candidate


def build_tree(directory: Path | None = None) -> list[dict]:
    current = directory or REPO_ROOT
    nodes: list[dict] = []
    for path in sorted(current.iterdir(), key=lambda item: (item.is_file(), item.name.lower())):
        if path.name.startswith(".") or path.name in {"node_modules", "__pycache__"}:
            continue
        relative = path.relative_to(REPO_ROOT).as_posix()
        node = {"name": path.name, "path": relative, "type": "folder" if path.is_dir() else "file"}
        if path.is_dir():
            node["children"] = build_tree(path)
        nodes.append(node)
    return nodes


def read_file(relative_path: str) -> dict:
    path = _safe_path(relative_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(relative_path)
    content = path.read_text(encoding="utf-8")
    return {
        "path": relative_path,
        "language": path.suffix.lstrip(".") or "text",
        "content": content,
        "lines": len(content.splitlines()),
    }


def repository_summary() -> dict:
    files = [path for path in REPO_ROOT.rglob("*") if path.is_file() and not path.name.startswith(".")]
    return {
        "name": "acme/expenseflow",
        "branch": "main",
        "commit": "8c4f1a2",
        "files": len(files),
        "services": 4,
        "languages": [{"name": "TypeScript", "value": 62}, {"name": "Python", "value": 31}, {"name": "Other", "value": 7}],
        "indexed_at": "2026-09-21T09:42:00Z",
    }


def context_for_llm(max_chars: int = 45_000) -> str:
    """Return bounded, line-numbered context from the simulated existing product."""
    priority = [
        "README.md",
        "docs/architecture.md",
        "docs/expense-workflow.md",
        "docs/decisions/ADR-014-immutable-submissions.md",
        "services/expense-api/app/routes/expenses.py",
        "services/expense-api/app/services/submission.py",
        "services/expense-api/app/models/expense.py",
        "services/expense-api/app/models/audit.py",
        "services/approval-service/app/policy.py",
        "services/approval-service/app/handlers.py",
        "services/notification-service/app/handlers.py",
        "apps/web/src/api/expenses.ts",
        "apps/web/src/features/expenses/ExpenseForm.tsx",
        "packages/shared-types/src/index.ts",
        "database/schema.sql",
    ]
    sections: list[str] = []
    total = 0
    for relative in priority:
        path = _safe_path(relative)
        if not path.exists():
            continue
        numbered = "\n".join(f"{index:>4}: {line}" for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1))
        section = f"\n--- FILE: {relative} ---\n{numbered}\n"
        if total + len(section) > max_chars:
            break
        sections.append(section)
        total += len(section)
    return "".join(sections)

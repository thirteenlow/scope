import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .models import Commit, Developer, Issue, PullRequest


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ModelT = TypeVar("ModelT", bound=BaseModel)


def _load(filename: str, model: type[ModelT]) -> list[ModelT]:
    raw = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
    return [model.model_validate(item) for item in raw]


def get_developers() -> list[Developer]:
    return _load("developers.json", Developer)


def get_issues() -> list[Issue]:
    return _load("issues.json", Issue)


def get_pull_requests() -> list[PullRequest]:
    return _load("pull_requests.json", PullRequest)


def get_commits() -> list[Commit]:
    return _load("commits.json", Commit)


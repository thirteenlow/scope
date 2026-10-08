import json
import os
import re

import httpx
from dotenv import load_dotenv

from .models import (
    AnalysisResult,
    ChatMessage,
    ScopeOption,
)
from .repository import context_for_llm


load_dotenv()

DEFAULT_BASE_URL = (
    "https://api.anthropic.com"
)
DEFAULT_MODEL = "claude-sonnet-5"


class LlmConfigurationError(
    RuntimeError
):
    pass


class LlmResponseError(RuntimeError):
    pass


def model_name() -> str:
    return os.getenv(
        "ANTHROPIC_MODEL",
        DEFAULT_MODEL,
    ).strip()


def anthropic_url() -> str:
    base_url = os.getenv(
        "ANTHROPIC_BASE_URL",
        DEFAULT_BASE_URL,
    ).strip().rstrip("/")

    if base_url.endswith("/v1"):
        return f"{base_url}/messages"

    return f"{base_url}/v1/messages"


def is_configured() -> bool:
    auth_token = os.getenv(
        "ANTHROPIC_AUTH_TOKEN",
        "",
    ).strip()

    api_key = os.getenv(
        "ANTHROPIC_API_KEY",
        "",
    ).strip()

    return bool(auth_token or api_key)


def _headers() -> dict[str, str]:
    auth_token = os.getenv(
        "ANTHROPIC_AUTH_TOKEN",
        "",
    ).strip()

    api_key = os.getenv(
        "ANTHROPIC_API_KEY",
        "",
    ).strip()

    if not auth_token and not api_key:
        raise LlmConfigurationError(
            "Claude is not configured. Add "
            "ANTHROPIC_AUTH_TOKEN or "
            "ANTHROPIC_API_KEY to "
            "backend/.env and restart the API."
        )

    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    if auth_token:
        headers["authorization"] = (
            f"Bearer {auth_token}"
        )
    else:
        headers["x-api-key"] = api_key

    return headers


async def _send_to_claude(
    payload: dict,
) -> dict:
    timeout = httpx.Timeout(
        connect=20.0,
        read=240.0,
        write=60.0,
        pool=20.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                anthropic_url(),
                headers=_headers(),
                json=payload,
            )

        response.raise_for_status()

    except httpx.ReadTimeout as exc:
        raise LlmResponseError(
            "Claude took too long to generate the PRD. "
            "Please try again; the selected scope and conversation are still saved."
        ) from exc

    except httpx.ConnectTimeout as exc:
        raise LlmResponseError(
            "Timed out while connecting to the Claude gateway."
        ) from exc

    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:1000]
        raise LlmResponseError(
            f"Claude gateway returned {exc.response.status_code}: {detail}"
        ) from exc

    except httpx.HTTPError as exc:
        raise LlmResponseError(
            f"Could not reach Claude: {type(exc).__name__}: {exc}"
        ) from exc

    return response.json()


def _extract_text(body: dict) -> str:
    text = "\n".join(
        block.get("text", "")
        for block in body.get(
            "content",
            [],
        )
        if block.get("type") == "text"
    ).strip()

    if not text:
        raise LlmResponseError(
            "Claude returned an empty response."
        )

    return text


def _system_prompt(
    mode: str,
    target_weeks: int,
) -> str:
    shared = f"""
You are Scope, a senior product-and-engineering
planning partner embedded in an existing product
named PocketPlan.

Your user is usually a product manager. Translate
product intent into technically credible plans
without pretending uncertain facts are verified.

PocketPlan is a personal budgeting app for
individuals. It is not an employee expense,
reimbursement, accounting, or organizational
approval product.

Rules:
- Ground every technical claim in the repository
  context below.
- Clearly distinguish verified code facts,
  reasonable inferences, and open questions.
- Use short, clear language.
- Do not overwhelm the PM with implementation
  trivia.
- Never claim that a Jira issue was created.
  The application handles that after human approval.
- The requested target is {target_weeks} weeks.
- Evidence paths must exactly match paths shown
  in repository context.

POCKETPLAN REPOSITORY CONTEXT:
{context_for_llm(max_chars=20_000)}
"""

    if mode == "chat":
        return shared + """
Respond conversationally using Markdown.

Help refine the feature. Ask at most two
high-value questions at a time.

If the request is already specific, summarize
your early read and tell the user they can click
Generate plan.

Do not output JSON in chat mode.
"""

    return shared + """
Generate an engineering-ready scope plan now.

Return ONLY one valid JSON object, without
Markdown fences or additional commentary,
matching this structure:

{
  "message": "Concise summary for the PM",
  "verdict": "Short feasibility verdict",
  "feasibility": 0,
  "timeline_confidence": 0,
  "risk": "low|medium|high",
  "summary": "Evidence-backed explanation",
  "affected_areas": ["area"],
  "evidence": [
    {
      "id": "EV-1",
      "type": "verified|inferred|question",
      "title": "...",
      "detail": "...",
      "path": "exact/path/or omit",
      "line": 1,
      "confidence": 0
    }
  ],
  "options": [
    {
      "id": "mvp",
      "name": "...",
      "duration": "...",
      "confidence": "high|medium|low",
      "summary": "...",
      "includes": ["..."],
      "excludes": ["..."],
      "recommended": true
    }
  ],
  "plan": [
    {
      "temp_key": "EPIC-1",
      "type": "Epic|Story|Task|Spike",
      "title": "...",
      "description": "...",
      "parent": null,
      "estimate": 8,
      "discipline": "product|frontend|backend|platform|qa|workflow",
      "evidence_ids": ["EV-1"]
    }
  ],
  "questions": ["remaining decision"]
}

Requirements:
- Include 2 or 3 genuinely different scope options.
- Create one Epic, 2-4 outcome-oriented Stories,
  and technical Tasks underneath them.
- Do not create separate frontend/backend epics.
- Make parent keys valid.
- Make estimates realistic.
- Use 4-8 evidence items.
- Prefer exact files and line numbers.
"""


async def talk_to_claude(
    messages: list[ChatMessage],
    mode: str,
    target_weeks: int,
) -> tuple[
    str,
    AnalysisResult | None,
    str,
]:
    # Validate credentials before constructing
    # and sending the request.
    _headers()

    model = model_name()

    api_messages = [
        message.model_dump()
        for message in messages
    ]

    # Remove the frontend's static welcome
    # assistant message.
    while (
        api_messages
        and api_messages[0]["role"]
        == "assistant"
    ):
        api_messages.pop(0)

    # Anthropic expects the conversation to
    # finish with a user message.
    if (
        api_messages
        and api_messages[-1]["role"]
        == "assistant"
    ):
        instruction = (
            "Generate the plan now using "
            "the decisions and constraints above."
            if mode == "plan"
            else "Continue."
        )

        api_messages.append(
            {
                "role": "user",
                "content": instruction,
            }
        )

    payload = {
        "model": model,
        "max_tokens": (
            1400
            if mode == "chat"
            else 7000
        ),
        "system": _system_prompt(
            mode,
            target_weeks,
        ),
        "messages": api_messages,
    }

    body = await _send_to_claude(
        payload
    )

    text = _extract_text(body)

    if mode == "chat":
        return text, None, model

    try:
        match = re.search(
            r"\{.*\}",
            text,
            re.DOTALL,
        )

        parsed = json.loads(
            match.group(0)
            if match
            else text
        )

        assistant_message = parsed.pop(
            "message",
            (
                "I generated an "
                "evidence-backed plan for "
                "engineering review."
            ),
        )

        parsed["feature_id"] = "FEAT-104"

        analysis = (
            AnalysisResult.model_validate(
                parsed
            )
        )

    except (
        json.JSONDecodeError,
        ValueError,
        AttributeError,
    ) as exc:
        raise LlmResponseError(
            "Claude responded, but its plan "
            "could not be validated. Please "
            "try Generate plan again."
        ) from exc

    return (
        assistant_message,
        analysis,
        model,
    )


async def generate_prd(
    messages: list[ChatMessage],
    analysis: AnalysisResult,
    selected_option: ScopeOption,
    target_weeks: int,
) -> tuple[str, str]:
    # Validate credentials before generating.
    _headers()

    conversation = "\n\n".join(
        (
            f"{message.role.upper()}: "
            f"{message.content}"
        )
        for message in messages
    )

    prompt = f"""
Create a complete Product Requirements Document
for PocketPlan using the approved scope below.

PocketPlan is a personal budgeting application
for individuals.

Do not describe PocketPlan as an employee expense,
reimbursement, accounting, or organizational
finance product.

APPROVED SCOPE

Name:
{selected_option.name}

Summary:
{selected_option.summary}

Delivery window:
{selected_option.duration}

Requested target:
{target_weeks} weeks

Confidence:
{selected_option.confidence}

Included:
{json.dumps(
    selected_option.includes,
    indent=2,
)}

Excluded:
{json.dumps(
    selected_option.excludes,
    indent=2,
)}

ENGINEERING ANALYSIS

{analysis.model_dump_json(indent=2)}

DISCOVERY CONVERSATION

{conversation}

REPOSITORY CONTEXT

{context_for_llm()}

Return polished Markdown only.

Use these exact sections:

# Product Requirements Document: [feature name]

## Document status

## Executive summary

## Problem and opportunity

## Goals

## Non-goals

## Target users and user needs

## User experience and primary flow

## Functional requirements

## Acceptance criteria

## Technical approach and affected systems

## Data, privacy and security

## Analytics and success metrics

## Dependencies

## Risks and mitigations

## Rollout plan

## Open questions

Requirements:

- Treat the selected scope as the source of truth.
- Make functional requirements numbered.
- Make acceptance criteria specific and testable.
- Include repository evidence paths where relevant.
- Do not invent verified product or code facts.
- Clearly label assumptions.
- Clearly label unresolved decisions.
- Use the excluded items to define non-goals.
- Include measurable success metrics.
- Include a phased rollout where appropriate.
- Keep the document useful to product, design,
  engineering and QA.
"""

    model = model_name()

    payload = {
        "model": model,
        "max_tokens": 3500,
        "system": (
            "You are Scope, a senior product "
            "manager and technical product writer. "
            "Produce a complete, precise PRD "
            "grounded in the supplied approved "
            "scope and repository evidence."
        ),
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    body = await _send_to_claude(
        payload
    )

    markdown = _extract_text(body)

    # Some gateways may still include Markdown
    # fences despite the prompt. Remove only an
    # outer Markdown fence.
    if (
        markdown.startswith("```markdown")
        and markdown.endswith("```")
    ):
        markdown = (
            markdown[len("```markdown"):-3]
            .strip()
        )
    elif (
        markdown.startswith("```")
        and markdown.endswith("```")
    ):
        markdown = (
            markdown[3:-3]
            .strip()
        )

    return markdown, model
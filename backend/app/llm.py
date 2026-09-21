import json
import os
import re

import httpx
from dotenv import load_dotenv

from .models import AnalysisResult, ChatMessage
from .repository import context_for_llm


# Loads variables from backend/.env
load_dotenv()

DEFAULT_BASE_URL = "https://api.anthropic.com"
DEFAULT_MODEL = "claude-sonnet-5"


class LlmConfigurationError(RuntimeError):
    pass


class LlmResponseError(RuntimeError):
    pass


def model_name() -> str:
    return os.getenv(
        "ANTHROPIC_MODEL",
        DEFAULT_MODEL,
    ).strip()


def anthropic_url() -> str:
    """
    Builds the Messages API URL.

    Examples:
    https://api.anthropic.com
        -> https://api.anthropic.com/v1/messages

    https://llm-gateway.aisg.sg/
        -> https://llm-gateway.aisg.sg/v1/messages
    """
    base_url = os.getenv(
        "ANTHROPIC_BASE_URL",
        DEFAULT_BASE_URL,
    ).strip().rstrip("/")

    # Also supports a base URL that already ends with /v1.
    if base_url.endswith("/v1"):
        return f"{base_url}/messages"

    return f"{base_url}/v1/messages"


def is_configured() -> bool:
    """
    Supports both:

    1. AISG or compatible gateway:
       ANTHROPIC_AUTH_TOKEN

    2. Direct Anthropic API:
       ANTHROPIC_API_KEY
    """
    auth_token = os.getenv(
        "ANTHROPIC_AUTH_TOKEN",
        "",
    ).strip()

    api_key = os.getenv(
        "ANTHROPIC_API_KEY",
        "",
    ).strip()

    return bool(auth_token or api_key)


def _system_prompt(mode: str, target_weeks: int) -> str:
    shared = f"""
You are Scope, a senior product-and-engineering planning partner embedded
in an existing product named ExpenseFlow.

Your user is usually a product manager. Translate product intent into
technically credible plans without pretending uncertain facts are verified.

Rules:

- Ground every technical claim in the repository context below.
- Clearly distinguish verified code facts, reasonable inferences, and
  open questions.
- Use short, clear language.
- Do not overwhelm the product manager with implementation trivia.
- Never claim that a Jira issue was created. The application handles Jira
  creation only after human approval.
- The requested target is {target_weeks} weeks.
- Evidence paths must exactly match paths shown in the repository context.
- Do not invent files, APIs, tables, services, or implementation details.

EXPENSEFLOW REPOSITORY CONTEXT:

{context_for_llm()}
"""

    if mode == "chat":
        return (
            shared
            + """
Respond conversationally in plain text.

Help the user refine the feature request. Ask at most two high-value
questions at a time.

Focus questions on decisions that materially affect:

- Engineering feasibility
- Scope
- Timeline
- Security
- Approval workflow
- Data integrity
- Web or mobile support

If the request is already sufficiently specific, provide a short initial
assessment and tell the user that they can click Generate plan.

Do not output JSON in chat mode.
"""
        )

    return (
        shared
        + """
Generate an engineering-ready scope plan now.

Return ONLY one valid JSON object.

Do not include Markdown fences, introductory text, or commentary outside
the JSON object.

Use this exact structure:

{
  "message": "A concise conversational summary for the product manager",
  "verdict": "Short feasibility verdict",
  "feasibility": 0,
  "timeline_confidence": 0,
  "risk": "low",
  "summary": "Evidence-backed explanation",
  "affected_areas": [
    "Area name"
  ],
  "evidence": [
    {
      "id": "EV-1",
      "type": "verified",
      "title": "Evidence title",
      "detail": "Evidence explanation",
      "path": "exact/repository/path",
      "line": 1,
      "confidence": 95
    }
  ],
  "options": [
    {
      "id": "mvp",
      "name": "Option name",
      "duration": "4 weeks",
      "confidence": "medium",
      "summary": "Option summary",
      "includes": [
        "Included item"
      ],
      "excludes": [
        "Excluded item"
      ],
      "recommended": true
    }
  ],
  "plan": [
    {
      "temp_key": "EPIC-1",
      "type": "Epic",
      "title": "Epic title",
      "description": "Epic description",
      "parent": null,
      "estimate": 8,
      "discipline": "product",
      "evidence_ids": [
        "EV-1"
      ]
    }
  ],
  "questions": [
    "Remaining product or engineering decision"
  ]
}

Validation requirements:

- risk must be one of: low, medium, high.
- evidence type must be one of: verified, inferred, question.
- option confidence must be one of: high, medium, low.
- plan item type must be one of: Epic, Story, Task, Spike.
- Include two or three genuinely different scope options.
- Include exactly one primary Epic.
- Include two to four outcome-oriented Stories.
- Add technical Tasks beneath the relevant Stories.
- Do not create separate frontend and backend epics.
- Every parent value must reference a valid temp_key.
- Use realistic estimates.
- Use four to eight evidence items.
- Prefer exact repository file paths and line numbers.
- Omit path and line when an item is an open product question.
"""
    )


def _prepare_messages(
    messages: list[ChatMessage],
    mode: str,
) -> list[dict[str, str]]:
    """
    Removes Scope's local welcome message when it appears before the first
    user message and ensures plan generation ends with a user instruction.
    """
    api_messages = [
        message.model_dump()
        for message in messages
    ]

    while (
        api_messages
        and api_messages[0]["role"] == "assistant"
    ):
        api_messages.pop(0)

    if not api_messages:
        raise LlmResponseError(
            "At least one user message is required."
        )

    if api_messages[-1]["role"] == "assistant":
        if mode == "plan":
            instruction = (
                "Generate the plan now using the decisions and "
                "constraints above."
            )
        else:
            instruction = "Continue the conversation."

        api_messages.append(
            {
                "role": "user",
                "content": instruction,
            }
        )

    return api_messages


def _authentication_headers() -> dict[str, str]:
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
            "Claude is not configured. Add ANTHROPIC_AUTH_TOKEN "
            "or ANTHROPIC_API_KEY to backend/.env, then restart "
            "the backend."
        )

    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    if auth_token:
        # Used by Claude Code and compatible gateways such as AISG.
        headers["authorization"] = f"Bearer {auth_token}"
    else:
        # Used by Anthropic's direct API.
        headers["x-api-key"] = api_key

    return headers


def _extract_text(response_body: dict) -> str:
    text_blocks = []

    for block in response_body.get("content", []):
        if block.get("type") == "text":
            text_blocks.append(block.get("text", ""))

    return "\n".join(text_blocks).strip()


def _parse_analysis(
    text: str,
) -> tuple[str, AnalysisResult]:
    """
    Extracts and validates the structured plan returned by Claude.
    """
    try:
        match = re.search(
            r"\{.*\}",
            text,
            re.DOTALL,
        )

        json_text = match.group(0) if match else text
        parsed = json.loads(json_text)

        assistant_message = parsed.pop(
            "message",
            (
                "I generated an evidence-backed plan "
                "for engineering review."
            ),
        )

        parsed["feature_id"] = "FEAT-104"

        analysis = AnalysisResult.model_validate(parsed)

        return assistant_message, analysis

    except (
        json.JSONDecodeError,
        ValueError,
        AttributeError,
        TypeError,
    ) as exc:
        raise LlmResponseError(
            "Claude responded, but the generated plan could not "
            "be validated. Please click Generate plan again."
        ) from exc


async def talk_to_claude(
    messages: list[ChatMessage],
    mode: str,
    target_weeks: int,
) -> tuple[str, AnalysisResult | None, str]:
    if not is_configured():
        raise LlmConfigurationError(
            "Claude is not configured. Add ANTHROPIC_AUTH_TOKEN "
            "or ANTHROPIC_API_KEY to backend/.env, then restart "
            "the backend."
        )

    model = model_name()
    api_messages = _prepare_messages(
        messages,
        mode,
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
        "messages": api_messages
    }

    headers = _authentication_headers()

    try:
        async with httpx.AsyncClient(
            timeout=120.0,
        ) as client:
            response = await client.post(
                anthropic_url(),
                headers=headers,
                json=payload,
            )

        response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code

        try:
            response_data = exc.response.json()
            detail = (
                response_data.get("error", {}).get("message")
                or response_data.get("message")
                or exc.response.text
            )
        except (ValueError, AttributeError):
            detail = exc.response.text

        raise LlmResponseError(
            f"Claude gateway returned {status_code}: "
            f"{str(detail)[:500]}"
        ) from exc

    except httpx.TimeoutException as exc:
        raise LlmResponseError(
            "The Claude request timed out. Please try again."
        ) from exc

    except httpx.HTTPError as exc:
        raise LlmResponseError(
            f"Could not reach the Claude gateway: {exc}"
        ) from exc

    try:
        response_body = response.json()
    except ValueError as exc:
        raise LlmResponseError(
            "The Claude gateway returned an invalid response."
        ) from exc

    text = _extract_text(response_body)

    if not text:
        raise LlmResponseError(
            "Claude returned an empty response."
        )

    if mode == "chat":
        return text, None, model

    assistant_message, analysis = _parse_analysis(text)

    return assistant_message, analysis, model
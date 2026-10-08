import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .models import AnalysisResult, ChatMessage


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "scope.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                target_weeks INTEGER NOT NULL DEFAULT 4,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL
                    REFERENCES conversations(id)
                    ON DELETE CASCADE,
                role TEXT NOT NULL
                    CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                position INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS plans (
                conversation_id TEXT PRIMARY KEY
                    REFERENCES conversations(id)
                    ON DELETE CASCADE,
                analysis_json TEXT NOT NULL,
                selected_option TEXT,
                prd_markdown TEXT,
                prd_model TEXT,
                prd_updated_at TEXT,
                jira_synced_at TEXT,
                jira_issue_keys TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id, position);
            """
        )

        # Automatically migrate an existing database.
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(plans)"
            ).fetchall()
        }

        optional_columns = (
            "prd_markdown",
            "prd_model",
            "prd_updated_at",
            "jira_synced_at",
            "jira_issue_keys",
        )

        for name in optional_columns:
            if name not in columns:
                connection.execute(
                    f"ALTER TABLE plans ADD COLUMN {name} TEXT"
                )
                
        # Repair titles shortened by older versions.
        title_rows = connection.execute(
            """
            SELECT c.id, m.content
            FROM conversations c
            JOIN messages m ON m.id = (
                SELECT first_message.id
                FROM messages first_message
                WHERE first_message.conversation_id = c.id
                AND first_message.role = 'user'
                ORDER BY first_message.position
                LIMIT 1
            )
            """
        ).fetchall()

        for row in title_rows:
            full_title = " ".join(row["content"].split())

            if full_title:
                connection.execute(
                    """
                    UPDATE conversations
                    SET title = ?
                    WHERE id = ?
                    """,
                    (full_title, row["id"]),
                )

                


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _title_from_messages(messages: list[ChatMessage]) -> str:
    first_user = next(
        (
            message.content.strip()
            for message in messages
            if message.role == "user"
        ),
        "New feature plan",
    )

    return " ".join(first_user.split())


def list_conversations() -> list[dict]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT
                c.*,
                COUNT(m.id) AS message_count,
                CASE
                    WHEN p.conversation_id IS NULL THEN 0
                    ELSE 1
                END AS has_plan
            FROM conversations c
            LEFT JOIN messages m
                ON m.conversation_id = c.id
            LEFT JOIN plans p
                ON p.conversation_id = c.id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """
        ).fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "target_weeks": row["target_weeks"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "message_count": row["message_count"],
            "has_plan": bool(row["has_plan"]),
        }
        for row in rows
    ]


def get_conversation(conversation_id: str) -> dict | None:
    with _connect() as connection:
        conversation = connection.execute(
            """
            SELECT *
            FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        ).fetchone()

        if not conversation:
            return None

        message_rows = connection.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY position
            """,
            (conversation_id,),
        ).fetchall()

        plan_row = connection.execute(
            """
            SELECT
                analysis_json,
                selected_option,
                prd_markdown,
                prd_model,
                prd_updated_at,
                jira_synced_at,
                jira_issue_keys
            FROM plans
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchone()

    jira_issue_keys: list[str] = []

    if plan_row:
        try:
            jira_issue_keys = json.loads(
                plan_row["jira_issue_keys"] or "[]"
            )
        except json.JSONDecodeError:
            jira_issue_keys = []

    return {
        "id": conversation["id"],
        "title": conversation["title"],
        "target_weeks": conversation["target_weeks"],
        "created_at": conversation["created_at"],
        "updated_at": conversation["updated_at"],
        "messages": [dict(row) for row in message_rows],
        "analysis": (
            json.loads(plan_row["analysis_json"])
            if plan_row
            else None
        ),
        "selected_option": (
            plan_row["selected_option"]
            if plan_row
            else None
        ),
        "prd_markdown": (
            plan_row["prd_markdown"]
            if plan_row
            else None
        ),
        "prd_model": (
            plan_row["prd_model"]
            if plan_row
            else None
        ),
        "prd_updated_at": (
            plan_row["prd_updated_at"]
            if plan_row
            else None
        ),
        "jira_synced_at": (
            plan_row["jira_synced_at"]
            if plan_row
            else None
        ),
        "jira_issue_keys": jira_issue_keys,
    }


def save_exchange(
    conversation_id: str | None,
    messages: list[ChatMessage],
    assistant_message: str,
    target_weeks: int,
    analysis: AnalysisResult | None,
) -> str:
    identifier = conversation_id or str(uuid4())
    now = _now()

    normalized = list(messages)

    # The permanent welcome message is frontend-only.
    while normalized and normalized[0].role == "assistant":
        normalized.pop(0)

    normalized.append(
        ChatMessage(
            role="assistant",
            content=assistant_message,
        )
    )

    with _connect() as connection:
        existing = connection.execute(
            """
            SELECT id
            FROM conversations
            WHERE id = ?
            """,
            (identifier,),
        ).fetchone()

        if existing:
            connection.execute(
                """
                UPDATE conversations
                SET title = ?,
                    target_weeks = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    _title_from_messages(normalized),
                    target_weeks,
                    now,
                    identifier,
                ),
            )
        else:
            connection.execute(
                """
                INSERT INTO conversations (
                    id,
                    title,
                    target_weeks,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    identifier,
                    _title_from_messages(normalized),
                    target_weeks,
                    now,
                    now,
                ),
            )

        connection.execute(
            """
            DELETE FROM messages
            WHERE conversation_id = ?
            """,
            (identifier,),
        )

        connection.executemany(
            """
            INSERT INTO messages (
                id,
                conversation_id,
                role,
                content,
                position,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(uuid4()),
                    identifier,
                    message.role,
                    message.content,
                    position,
                    now,
                )
                for position, message in enumerate(normalized)
            ],
        )

        if analysis:
            connection.execute(
                """
                INSERT INTO plans (
                    conversation_id,
                    analysis_json,
                    updated_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(conversation_id) DO UPDATE SET
                    analysis_json = excluded.analysis_json,
                    selected_option = NULL,
                    prd_markdown = NULL,
                    prd_model = NULL,
                    prd_updated_at = NULL,
                    jira_synced_at = NULL,
                    jira_issue_keys = NULL,
                    updated_at = excluded.updated_at
                """,
                (
                    identifier,
                    analysis.model_dump_json(),
                    now,
                ),
            )

    return identifier


def select_plan_option(
    conversation_id: str,
    option_id: str,
) -> None:
    """
    Preserve generated artifacts when the same option is selected again.

    If the PM changes to a different scope option, invalidate the PRD and
    Jira sync state because those artifacts describe the previous scope.
    """
    with _connect() as connection:
        connection.execute(
            """
            UPDATE plans
            SET
                prd_markdown =
                    CASE
                        WHEN selected_option = ? THEN prd_markdown
                        ELSE NULL
                    END,
                prd_model =
                    CASE
                        WHEN selected_option = ? THEN prd_model
                        ELSE NULL
                    END,
                prd_updated_at =
                    CASE
                        WHEN selected_option = ? THEN prd_updated_at
                        ELSE NULL
                    END,
                jira_synced_at =
                    CASE
                        WHEN selected_option = ? THEN jira_synced_at
                        ELSE NULL
                    END,
                jira_issue_keys =
                    CASE
                        WHEN selected_option = ? THEN jira_issue_keys
                        ELSE NULL
                    END,
                selected_option = ?,
                updated_at = ?
            WHERE conversation_id = ?
            """,
            (
                option_id,
                option_id,
                option_id,
                option_id,
                option_id,
                option_id,
                _now(),
                conversation_id,
            ),
        )


def save_prd(
    conversation_id: str,
    markdown: str,
    model: str,
) -> None:
    now = _now()

    with _connect() as connection:
        connection.execute(
            """
            UPDATE plans
            SET prd_markdown = ?,
                prd_model = ?,
                prd_updated_at = ?,
                updated_at = ?
            WHERE conversation_id = ?
            """,
            (
                markdown,
                model,
                now,
                now,
                conversation_id,
            ),
        )


def save_jira_sync(
    conversation_id: str,
    issue_keys: list[str],
) -> str:
    now = _now()

    with _connect() as connection:
        connection.execute(
            """
            UPDATE plans
            SET jira_synced_at = ?,
                jira_issue_keys = ?,
                updated_at = ?
            WHERE conversation_id = ?
            """,
            (
                now,
                json.dumps(issue_keys),
                now,
                conversation_id,
            ),
        )

    return now


def delete_conversation(conversation_id: str) -> bool:
    with _connect() as connection:
        cursor = connection.execute(
            """
            DELETE FROM conversations
            WHERE id = ?
            """,
            (conversation_id,),
        )

    return cursor.rowcount > 0


initialize_database()
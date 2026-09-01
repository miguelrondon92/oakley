"""SQLite conversation persistence."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oakley.config import get_settings, resolve_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New conversation',
    source_type TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    citations_json TEXT,
    answer_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, created_at);
"""


@dataclass
class Conversation:
    id: str
    title: str
    source_type: str | None
    created_at: str
    updated_at: str


@dataclass
class Message:
    id: str
    conversation_id: str
    role: str
    content: str
    citations_json: str | None
    answer_json: str | None
    created_at: str

    def citations(self) -> list[dict[str, Any]]:
        if not self.citations_json:
            return []
        return json.loads(self.citations_json)

    def answer(self) -> dict[str, Any] | None:
        if not self.answer_json:
            return None
        return json.loads(self.answer_json)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path() -> Path:
    settings = get_settings()
    raw = Path(getattr(settings, "db_path", Path("data/oakley.db")))
    return resolve_path(raw, settings)


def get_connection() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def _row_to_conversation(row: sqlite3.Row) -> Conversation:
    return Conversation(
        id=row["id"],
        title=row["title"],
        source_type=row["source_type"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_message(row: sqlite3.Row) -> Message:
    return Message(
        id=row["id"],
        conversation_id=row["conversation_id"],
        role=row["role"],
        content=row["content"],
        citations_json=row["citations_json"],
        answer_json=row["answer_json"],
        created_at=row["created_at"],
    )


def create_conversation(title: str = "New conversation", source_type: str | None = None) -> Conversation:
    init_db()
    conv_id = str(uuid.uuid4())
    now = _now_iso()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (id, title, source_type, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conv_id, title, source_type, now, now),
        )
        conn.commit()
    return Conversation(id=conv_id, title=title, source_type=source_type, created_at=now, updated_at=now)


def list_conversations() -> list[Conversation]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
    return [_row_to_conversation(r) for r in rows]


def get_conversation(conv_id: str) -> Conversation | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    return _row_to_conversation(row) if row else None


def update_conversation(
    conv_id: str,
    *,
    title: str | None = None,
    source_type: str | None = ...,  # type: ignore[assignment]
) -> Conversation | None:
    init_db()
    conv = get_conversation(conv_id)
    if not conv:
        return None
    new_title = conv.title if title is None else title
    if source_type is ...:
        new_source = conv.source_type
    else:
        new_source = source_type
    now = _now_iso()
    with get_connection() as conn:
        conn.execute(
            "UPDATE conversations SET title = ?, source_type = ?, updated_at = ? WHERE id = ?",
            (new_title, new_source, now, conv_id),
        )
        conn.commit()
    return Conversation(
        id=conv_id,
        title=new_title,
        source_type=new_source,
        created_at=conv.created_at,
        updated_at=now,
    )


def delete_conversation(conv_id: str) -> bool:
    init_db()
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()
        return cur.rowcount > 0


def list_messages(conv_id: str) -> list[Message]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,),
        ).fetchall()
    return [_row_to_message(r) for r in rows]


def add_message(
    conv_id: str,
    role: str,
    content: str,
    citations: list[dict[str, Any]] | None = None,
    answer: dict[str, Any] | None = None,
) -> Message:
    init_db()
    msg_id = str(uuid.uuid4())
    now = _now_iso()
    citations_json = json.dumps(citations) if citations else None
    answer_json = json.dumps(answer) if answer else None
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO messages (id, conversation_id, role, content, citations_json, answer_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, conv_id, role, content, citations_json, answer_json, now),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conv_id),
        )
        conn.commit()
    return Message(
        id=msg_id,
        conversation_id=conv_id,
        role=role,
        content=content,
        citations_json=citations_json,
        answer_json=answer_json,
        created_at=now,
    )


def message_history_for_rag(conv_id: str, exclude_latest: bool = False) -> list[dict[str, str]]:
    """Return {role, content} list for RAG prompt (prior turns only if exclude_latest)."""
    messages = list_messages(conv_id)
    if exclude_latest and messages:
        messages = messages[:-1]
    return [{"role": m.role, "content": m.content} for m in messages if m.content.strip()]


def auto_title_from_message(text: str, max_len: int = 60) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= max_len:
        return one_line or "New conversation"
    return one_line[: max_len - 1].rstrip() + "…"

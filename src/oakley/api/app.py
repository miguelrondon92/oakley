"""FastAPI application for Oakley chat."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.responses import Response
from starlette.types import Scope

from oakley.config import get_settings
from oakley.db import store as db
from oakley.rag.answer import ask_question
from oakley.vector.store import collection_count

logger = logging.getLogger(__name__)

app = FastAPI(title="Oakley", version="0.2.0")


class CreateConversationBody(BaseModel):
    title: str | None = None
    source_type: str | None = None


class UpdateConversationBody(BaseModel):
    title: str | None = None
    source_type: str | None = None


class PostMessageBody(BaseModel):
    content: str = Field(..., min_length=1)


class DevStaticFiles(StaticFiles):
    """Serve static assets; disable long-lived cache for JS/CSS during local dev."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if path.endswith((".js", ".css")):
            response.headers["Cache-Control"] = "no-cache"
        return response


def _static_root() -> Path:
    return get_settings().root


def _conversation_dict(conv: db.Conversation) -> dict[str, Any]:
    return {
        "id": conv.id,
        "title": conv.title,
        "source_type": conv.source_type,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
    }


def _message_dict(msg: db.Message) -> dict[str, Any]:
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "role": msg.role,
        "content": msg.content,
        "citations": msg.citations(),
        "answer": msg.answer(),
        "created_at": msg.created_at,
    }


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/api/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    count = collection_count()
    return {
        "status": "ok",
        "gemini_configured": settings.gemini_configured,
        "indexed_chunks": count if count is not None else 0,
    }


@app.get("/api/conversations")
def list_conversations() -> list[dict[str, Any]]:
    return [_conversation_dict(c) for c in db.list_conversations()]


@app.post("/api/conversations", status_code=201)
def create_conversation(body: CreateConversationBody) -> dict[str, Any]:
    conv = db.create_conversation(
        title=body.title or "New conversation",
        source_type=body.source_type,
    )
    return _conversation_dict(conv)


@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str) -> dict[str, Any]:
    conv = db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.list_messages(conv_id)
    return {
        **_conversation_dict(conv),
        "messages": [_message_dict(m) for m in messages],
    }


@app.patch("/api/conversations/{conv_id}")
def patch_conversation(conv_id: str, body: UpdateConversationBody) -> dict[str, Any]:
    conv = db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    updates = body.model_dump(exclude_unset=True)
    conv = db.update_conversation(
        conv_id,
        title=updates.get("title"),
        source_type=updates["source_type"] if "source_type" in updates else ...,
    )
    return _conversation_dict(conv)  # type: ignore[arg-type]


@app.delete("/api/conversations/{conv_id}", status_code=204)
def delete_conversation(conv_id: str) -> None:
    if not db.delete_conversation(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")


@app.post("/api/conversations/{conv_id}/messages", status_code=201)
def post_message(conv_id: str, body: PostMessageBody) -> dict[str, Any]:
    conv = db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    history = db.message_history_for_rag(conv_id)
    user_msg = db.add_message(conv_id, "user", body.content.strip())

    if conv.title == "New conversation":
        db.update_conversation(conv_id, title=db.auto_title_from_message(body.content))

    try:
        result = ask_question(
            body.content.strip(),
            source_type=conv.source_type,
            history=history,
        )
    except RuntimeError as exc:
        logger.warning("RAG service error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="RAG service unavailable. Check GEMINI_API_KEY and try again.",
        ) from exc

    assistant_msg = db.add_message(
        conv_id,
        "assistant",
        result["answer"],
        citations=result.get("citations"),
        answer=result,
    )

    return {
        "user_message": _message_dict(user_msg),
        "assistant_message": _message_dict(assistant_msg),
    }


static_dir = _static_root() / "static"
templates_dir = _static_root() / "templates"

if static_dir.exists():
    app.mount("/static", DevStaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def index() -> FileResponse:
    page = templates_dir / "chat.html"
    if not page.exists():
        raise HTTPException(status_code=500, detail="Chat template missing")
    return FileResponse(page)

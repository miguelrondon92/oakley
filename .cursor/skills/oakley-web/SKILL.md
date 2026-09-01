---
name: oakley-web
description: Build Oakley web chat UI, FastAPI routes, and conversation persistence. Use when working on src/oakley/api/, templates/, static/, SQLite conversations, or oakley serve.
---

# Oakley Web / API

## Scope

`src/oakley/api/`, `src/oakley/db/`, `templates/`, `static/`, `oakley serve`.

## Responsibilities

1. FastAPI REST API for conversations and messages
2. SQLite persistence (`data/oakley.db`)
3. Rich chat UI: sidebar, source toggle, citation cards
4. Wire messages to `ask_question(..., history=...)` — retrieval unchanged
5. `oakley serve` via uvicorn

## Rules

- **Do not** duplicate RAG logic in routes — call `oakley.rag.answer`
- **Do not** read or log `.env` / API keys
- **Do not** change retrieval/routing unless explicitly assigned
- Persist full answer-contract JSON on assistant messages

## API summary

| Route | Purpose |
|-------|---------|
| `GET /` | Chat page |
| `GET /api/health` | Status |
| `GET/POST /api/conversations` | List / create |
| `GET/PATCH/DELETE /api/conversations/{id}` | Thread CRUD |
| `POST /api/conversations/{id}/messages` | Send message |

## References

- `.cursor/resources/conversation-contract.md`
- `.cursor/resources/answer-contract.md`

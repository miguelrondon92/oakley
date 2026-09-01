# Oakley Conversation Contract

API and persistence shapes for multi-turn chat.

## Conversation object

```json
{
  "id": "uuid",
  "title": "Can I build a treehouse…",
  "source_type": null,
  "created_at": "2026-08-29T19:00:00+00:00",
  "updated_at": "2026-08-29T19:05:00+00:00"
}
```

`source_type`: `null` (all) | `hoa_bylaw` | `county_regulation`

## Message object

```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "role": "user",
  "content": "Can I build a treehouse?",
  "citations": [],
  "answer": null,
  "created_at": "2026-08-29T19:00:00+00:00"
}
```

Assistant messages include `citations[]` and full `answer` (answer-contract shape).

## POST /api/conversations/{id}/messages

Request:

```json
{ "content": "What about ACC approval?" }
```

Response:

```json
{
  "user_message": { /* Message */ },
  "assistant_message": { /* Message with answer + citations */ }
}
```

## RAG behavior

- **Retrieval:** latest user message only (unchanged from CLI)
- **Generation:** prior turns included in prompt (up to 10 messages / 4000 chars)
- **Persistence:** SQLite `data/oakley.db` (gitignored)

## UI

- Local only: `oakley serve` → `http://127.0.0.1:8080`
- Source toggle updates conversation `source_type` via PATCH

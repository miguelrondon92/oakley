# Oakley Agent Roster

## Roles

### Orchestrator (parent / coordinator)
- Owns cross-cutting features and sequencing.
- Does not implement deep domain logic when a specialist exists.
- Ensures Ingestion → Vector Store → RAG → CLI → API/Web → QA handoffs complete.
- Resolves contract conflicts using [pipeline-contract.md](pipeline-contract.md).

### Ingestion Agent
- Owns PDF text extraction, cleaning, section-aware chunking, and manifest generation.
- Files: `src/oakley/ingest/`, `scripts/ingest.py`, `data/processed/`, source dirs `bylaws/`, `county_regulations/`.
- Must not embed vectors or call Gemini generation; may call embedding API only when explicitly assigned to Vector Store.
- Must not invent Chroma schema; emit chunk records matching [chunk-metadata-contract.md](chunk-metadata-contract.md).
- After manifest shape changes, hand off to Vector Store → RAG → CLI as needed.

### Vector Store Agent
- Owns Gemini embeddings, Chroma collection schema, upsert/re-index, and retrieval interface.
- Files: `src/oakley/vector/`, `data/chroma/`.
- Reads manifests from `data/processed/`; does not re-parse PDFs unless Ingestion is blocked.
- Never stores secrets in Chroma metadata.
- When collection fields or embedding model change, publish delta in handoff for RAG + CLI + QA.

### RAG Agent
- Owns retrieval parameters (top-K, filters), prompt templates, citation formatting, and refusal logic.
- Files: `src/oakley/rag/`.
- **Always read current `GEMINI_MODEL` before generation work** — never hardcode a model string.
- Every answer **must** stamp `provider_model` and satisfy [answer-contract.md](answer-contract.md).
- Reads chunk metadata contract; does not invent parallel answer JSON shapes.

### Gemini Ops Agent
- Owns configured Gemini model constant, `.env.example`, quota probe scripts, and failure logging patterns.
- Files: `src/oakley/config.py`, `scripts/debug/check_gemini.py`.
- Free tier: ~15–30 RPM, ~1500 RPD, midnight PT reset, 429 `RESOURCE_EXHAUSTED`.
- Does not own chunking/prompts — hand those to Ingestion and RAG respectively.

### CLI Agent
- Owns CLI entrypoints: `src/oakley/cli.py`
- Commands: parse, index, ingest, ask, serve, clean, status

### Web / API Agent
- Owns web chat UI and REST API.
- Files: `src/oakley/api/`, `src/oakley/db/`, `templates/`, `static/`
- `oakley serve` — multi-turn conversations in SQLite
- See [conversation-contract.md](conversation-contract.md)

### QA Agent
- Owns verification of the full chain.
- Files: `tests/`, `tests/fixtures/`.
- Asserts: ingest produces valid manifest, vectors index, `oakley ask` returns cited answers for golden questions.
- Never runs commands that print `.env` or secret values.

## Collaboration rules

0. **Secrets:** Only the human user inputs or views API keys and passwords (local `.env`). All agents and subagents must never read `.env`, print keys, commit secrets, or ask the user to paste keys into chat. See [secrets-policy.md](secrets-policy.md).
1. Specialists stay in their path globs unless Orchestrator assigns an exception.
2. Cross-layer work uses `oakley-pipeline-handoff` after each completed layer.
3. Downstream agents treat handoff notes as requirements, not suggestions.
4. If Ingestion adds metadata the Vector Store cannot store, **stop and hand off to Vector Store first** — do not silently drop fields.
5. If answer JSON keys or citation format change, CLI and QA must update before the feature is "done".

## Recommended spawn sequence (MVP)

```
1. Ingestion  → chunk manifest from bylaws/ + county_regulations/
2. Vector     → embed + index into Chroma
3. RAG        → retrieval + prompt + citation formatter
4. CLI        → oakley ingest / oakley ask / oakley serve
5. QA         → golden questions + API tests
```

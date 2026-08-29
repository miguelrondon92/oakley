---
name: oakley-cli
description: Build Oakley CLI and later API entrypoints for ingest and ask commands. Use when working on src/oakley/cli.py, scripts/query.py, or Phase 2 API routes.
---

# Oakley CLI / API

## Scope

Phase 1: `src/oakley/cli.py`, `scripts/query.py`, `pyproject.toml` entry point `oakley`.
Phase 2: `src/oakley/api/`, `templates/`, `static/`.

## Phase 1 commands

| Command | Behavior |
|---------|----------|
| `oakley ingest [--source bylaws\|county\|all]` | Run ingestion + vector index (or ingest-only with flag) |
| `oakley ask "question" [--source-type hoa_bylaw\|county_regulation] [--json]` | RAG query |
| `oakley status` | Manifest + Chroma stats (chunk count, last ingest) |

## Responsibilities

1. Wire CLI args to Ingestion, Vector Store, and RAG services.
2. Pretty-print answers (default) or emit JSON (`--json`).
3. Exit codes: 0 success, 1 user error, 2 infrastructure/Gemini failure.
4. Phase 2: FastAPI `/ask` endpoint + minimal chat page.

## Rules

- **Do not** duplicate RAG logic in CLI — call `src/oakley/rag/`.
- **Do not** hardcode API keys.
- **Do not** parse PDFs in CLI when Ingestion module exists.
- Secrets: never open `.env`.

## Downstream handoff triggers

| Change | Notify |
|--------|--------|
| New CLI flag affecting filters | RAG, QA |
| Output format change | QA |
| New HTTP endpoint | QA, update agent roster for API/Web |

## References

- `.cursor/resources/answer-contract.md`
- `.cursor/resources/pipeline-contract.md`

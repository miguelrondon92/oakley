---
name: oakley-gemini-ops
description: Configure Gemini model, env templates, and quota handling for Oakley. Use when working on GEMINI_MODEL, .env.example, quota probe scripts, or Gemini failure logging.
---

# Oakley Gemini Ops

## Scope

`src/oakley/config.py`, `.env.example`, `scripts/debug/check_gemini.py`, Gemini-related logging.

## Responsibilities

1. Maintain `.env.example` with required vars (`GEMINI_API_KEY`, `GEMINI_MODEL`, `CHROMA_PERSIST_DIR`, `OAKLEY_TOP_K`).
2. Centralize `GEMINI_MODEL` in config (default: `gemini-2.0-flash` or current Flash-class model).
3. Document free-tier limits (~15–30 RPM, ~1500 RPD, midnight PT reset).
4. Provide quota probe script for developers (without printing key values).
5. Define structured failure log format: `OAKLEY_GEMINI_FAILURE class=... detail=...`

## Failure classes

| Class | Handling |
|-------|----------|
| `missing_key` | Clear setup message pointing to `.env.example` |
| `quota_429` | Backoff + user retry guidance |
| `model_error` | Log model name, suggest checking `GEMINI_MODEL` |
| `empty_embedding` | Skip chunk, log chunk_id |
| `empty_generation` | RAG returns refused answer |

## Rules

- **Do not** own chunking or RAG prompts — hand to Ingestion / RAG.
- **Do not** read or write `.env`; maintain `.env.example` with placeholders only.
- **Do not** print API keys in quota scripts — report configured yes/no only.
- Quota probe may call Gemini with a minimal request if key is set at runtime; never log the key or Authorization header.
- Changing `GEMINI_MODEL` requires noting re-index is **not** required for embeddings (embedding model is separate) but answers will stamp new model going forward.
- If embedding model changes, notify Vector Store for full re-index.

## References

- `.cursor/resources/pipeline-contract.md`
- `.cursor/resources/answer-contract.md` (`provider_model` field)
- `.cursor/resources/secrets-policy.md`

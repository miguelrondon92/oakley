# Oakley Agentic Development System

Multi-agent architecture for developing Oakley end-to-end: PDF ingestion → chunk manifest → Chroma vector store → Gemini RAG → CLI → (Phase 2) web chat.

Full details live under [`.cursor/`](.cursor/). Start with [`.cursor/resources/agent-roster.md`](.cursor/resources/agent-roster.md) and [`.cursor/resources/pipeline-contract.md`](.cursor/resources/pipeline-contract.md).

## Product scope

Oakley is an AI assistant for **local governing-entity regulations** — starting with **Oakwood Glen HOA** (Harris County, TX) bylaws and policies plus **Harris County** regulations. Source PDFs live in [`bylaws/`](bylaws/) and [`county_regulations/`](county_regulations/).

## Non-negotiable: secrets

**No agent may read, write, print, commit, log, or expose private keys, API keys, passwords, or secret-bearing files — ever.**

**Only the human user inputs secrets.** Agents use `.env.example` for documentation and tell the user to copy it to `.env` and fill in values locally. Agents never open `.env`, never paste keys into code or chat, and never push secrets to GitHub.

Full policy: [`.cursor/resources/secrets-policy.md`](.cursor/resources/secrets-policy.md)

Blocked paths include `.env`, `*.pem`, `*.key`, credential JSON, and production env files. Hooks enforce this at session start, file read, shell, write, and prompt time; agents must also refuse if asked.

### Agent checklist

- Document env **variable names** only (e.g. `GEMINI_API_KEY`)
- Refuse `cat .env`, `printenv`, or "show me my API key"
- Before `git commit`, ensure `.env` and key material are not staged
- Pass the secrets ban to every subagent you spawn
- Never put secrets in handoff files, tests, fixtures, or logs

## Pipeline (source of truth)

```
bylaws/ + county_regulations/  (PDF sources)
        ↓
Ingestion: extract → section-aware chunk → chunk_manifest.json
        ↓
Vector Store: Gemini text-embedding-004 → Chroma (data/chroma/)
        ↓
RAG: retrieve top-K → Gemini answer + citations
        ↓
CLI: oakley ingest | oakley ask "..."
        ↓
Web: oakley serve → multi-turn chat (SQLite)
        ↓
QA: golden Q&A fixtures against known doc sections
```

Any upstream schema or metadata change **must** propagate through this chain via the handoff protocol. Contract: [`.cursor/resources/pipeline-contract.md`](.cursor/resources/pipeline-contract.md).

## Gemini contingency

When Gemini calls fail (missing key, model error, quota, empty embedding):

1. **Users** — return a clear error; do not invent answers or citations. RAG must refuse when retrieval confidence is low.
2. **Logs** — emit structured log lines (`OAKLEY_GEMINI_FAILURE class=...`) for ops debugging; never log API key values.
3. **Rate limits** — Google AI Studio free tier ~15–30 RPM; handle 429 `RESOURCE_EXHAUSTED` with backoff and user-facing retry guidance.
4. **Model provenance** — stamp `provider_model` on every answer record from env `GEMINI_MODEL`; read current model before RAG work.

## Agent roster

| Agent | Focus | Primary paths |
|-------|--------|----------------|
| **Orchestrator** | Cross-cutting features, handoffs, conflict resolution | whole repo (coordination only) |
| **Ingestion** | PDF extract, clean, chunk, manifest | `src/oakley/ingest/`, `scripts/ingest.py`, `data/processed/` |
| **Vector Store** | Embeddings, Chroma schema, re-index | `src/oakley/vector/`, `data/chroma/` |
| **RAG** | Retrieval params, prompts, citation rules | `src/oakley/rag/` |
| **Gemini Ops** | `GEMINI_MODEL`, quota probes, `.env.example` | `src/oakley/config.py`, `scripts/debug/check_gemini.py` |
| **CLI / API** | User-facing entrypoints | `src/oakley/cli.py`, `src/oakley/api/`, `templates/`, `static/` |
| **QA** | Golden Q&A fixtures, ingest/query regression | `tests/`, `tests/fixtures/` |

## How to run work

1. Load skill `oakley-orchestrate` for multi-layer changes.
2. Spawn specialized subagents (or sequential turns) per layer touched.
3. After each layer finishes, run skill `oakley-pipeline-handoff` and notify the next owner.
4. QA validates citations and golden answers before closing.

## Skills

| Skill | When |
|-------|------|
| `oakley-orchestrate` | Feature spans 2+ layers |
| `oakley-ingest` | PDF parsing / chunking / manifest |
| `oakley-vector` | Chroma collections / embedding / re-index |
| `oakley-rag` | Retrieval tuning / prompts / citations |
| `oakley-gemini-ops` | Model constant / quota / failure handling |
| `oakley-cli` | CLI commands |
| `oakley-web` | Web chat UI / API / conversations |
| `oakley-pipeline-handoff` | After any layer change that affects downstream |
| `oakley-qa` | Verification and regression |

## Docs map

- Product overview: [`README.md`](README.md)
- Corpus catalog: [`.cursor/resources/corpus-inventory.md`](.cursor/resources/corpus-inventory.md)
- Chunk metadata: [`.cursor/resources/chunk-metadata-contract.md`](.cursor/resources/chunk-metadata-contract.md)
- Answer shape: [`.cursor/resources/answer-contract.md`](.cursor/resources/answer-contract.md)
- Agent roster: [`.cursor/resources/agent-roster.md`](.cursor/resources/agent-roster.md)
- Secrets policy: [`.cursor/resources/secrets-policy.md`](.cursor/resources/secrets-policy.md)

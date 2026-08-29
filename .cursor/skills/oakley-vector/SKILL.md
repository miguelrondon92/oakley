---
name: oakley-vector
description: Embed Oakley chunk manifests into Chroma with Gemini embeddings. Use when working on vector indexing, Chroma collections, re-index scripts, or src/oakley/vector/.
---

# Oakley Vector Store

## Scope

`src/oakley/vector/`, `data/chroma/`, embedding batch scripts.

## Responsibilities

1. Read latest (or specified) chunk manifest from `data/processed/`.
2. Batch-embed chunk text via Gemini `text-embedding-004`.
3. Upsert into Chroma collection `oakley_corpus` (configurable) with flat metadata.
4. Delete orphan vectors on full re-index when chunk_ids drop out of manifest.
5. Expose retrieval function for RAG: `search(query_embedding, top_k, filters)`.

## Rules

- **Do not** re-parse PDFs; consume manifests from Ingestion.
- **Do not** change chunk metadata semantics; request Ingestion handoff if fields missing.
- Chroma metadata must be flat (strings/ints/floats only).
- Vector ID = `chunk_id` from manifest.
- Secrets: never open `.env`; use app config that loads env at runtime.
- Respect Gemini rate limits; batch embeddings with backoff on 429.

## Environment

| Variable | Default |
|----------|---------|
| `CHROMA_PERSIST_DIR` | `data/chroma/` |
| `GEMINI_API_KEY` | required for embeddings |

## Downstream handoff triggers

| Change | Notify |
|--------|--------|
| Collection name or persist path change | RAG, CLI, `.env.example`, QA |
| Embedding model change | RAG (re-index required), Gemini Ops, QA |
| New metadata field in Chroma | RAG (prompt context), update pipeline-contract |
| Retrieval API signature change | RAG, CLI |

## References

- `.cursor/resources/pipeline-contract.md`
- `.cursor/resources/chunk-metadata-contract.md`

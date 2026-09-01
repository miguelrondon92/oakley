# Oakley Pipeline Contract

Shared contract between Ingestion, Vector Store, RAG, CLI, and QA agents.
Update this file when a layer changes the data shape; then run `oakley-pipeline-handoff`.

## End-to-end flow

```
[Sources] hoa_docs/** (PDF + MD) + county_regulations/*.pdf
        │  Registry: config.CORPUS_ROOTS + corpus-inventory.md
        ▼
[Ingestion] Per-file incremental parse (content-hash reuse, path-move detection)
        │  PDF: PyMuPDF extract → section-aware chunk
        │  MD: heading-based chunk (content_format=markdown)
        │  Output: data/processed/<manifest_id>/chunk_manifest.json
        │  Pointer: data/processed/latest.json (+ previous_manifest_id)
        ▼
[Vector Store] Gemini gemini-embedding-001 → Chroma persist (data/chroma/)
        │  Incremental index: embed only new/changed chunks; metadata-only upsert on moves
        │  --prune-orphans removes stale chunk_ids (default on)
        ▼
[RAG] Query embed → top-K retrieve → Gemini generate
        │  Output: answer-contract.md
        │  Refuse when no relevant chunks or low confidence
        ▼
[CLI] oakley ingest | oakley ask "question" [--source-type hoa_bylaw|county_regulation]
        │  Phase 2: HTTP API + chat UI
        ▼
[QA] Golden fixtures assert answer text + citations match known sections
```

## Identity keys (immutable)

- **Chunk ID:** `{source_type}:{content_hash}:{chunk_index}` (URL-safe, stable across re-ingest if text unchanged)
- **Manifest ID:** ISO date + short hash of source file list, e.g. `20260829-a1b2c3`
- **Document key:** `(source_type, source_file)` — basename of PDF under source dir

## Versioning rules

- Re-ingest creates a new manifest directory under `data/processed/`; Vector Store upserts by `chunk_id`.
- **Incremental parse:** reuse chunks when per-file `content_hash` unchanged; detect moved files (same hash, new path) without re-extract/re-embed.
- Orphan vectors (chunk_id no longer in latest manifest) should be deleted on re-index (`--prune-orphans`, default).
- Do not mutate historical manifest JSON; write new manifest per ingest run.
- `latest.json` stores `previous_manifest_id` for incremental index comparisons.

## Chroma record shape

| Field | Location | Notes |
|-------|----------|-------|
| `id` | Chroma id | = `chunk_id` |
| `document` | Chroma document | chunk `text` |
| `embedding` | Chroma embedding | from `models/gemini-embedding-001` |
| `metadata` | Chroma metadata | flat chunk metadata including `content_format`, `doc_category`, optional `context_doc_*` |

Chroma metadata must be flat. Serialize lists as comma-separated strings if needed.

## Retrieval payload (RAG internal)

```json
{
  "query": "user question",
  "chunks": [
    {
      "chunk_id": "...",
      "text": "...",
      "score": 0.87,
      "source_file": "...",
      "document_title": "...",
      "page_start": 3,
      "page_end": 4,
      "section_heading": "...",
      "source_type": "hoa_bylaw"
    }
  ],
  "filters": {
    "source_type": "hoa_bylaw"
  }
}
```

## Answer JSON (minimum keys CLI/QA may rely on)

See [answer-contract.md](answer-contract.md).

## Ingestion parameters (defaults)

| Parameter | Default |
|-----------|---------|
| `target_tokens` | 800 |
| `overlap_tokens` | 100 |
| `min_chunk_chars` | 100 |
| Extractor | PyMuPDF (`pymupdf`) |

Low text-density pages (< 50 chars) should be flagged `needs_ocr: true` in manifest stats; OCR is out of MVP scope.

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` | yes | Embeddings + generation |
| `GEMINI_MODEL` | yes | Generation model name |
| `CHROMA_PERSIST_DIR` | no | Default `data/chroma/` |
| `OAKLEY_TOP_K` | no | Default 5 |

Never commit `.env`. Reference `.env.example` only. **User inputs all secret values locally** — agents document variable names only. See [secrets-policy.md](secrets-policy.md).

## Cross-layer gates

- **Ingestion complete** when `chunk_manifest.json` validates against chunk-metadata-contract and manifest stats are logged.
- **Vector index ready** when all manifest chunk_ids exist in Chroma with embeddings.
- **RAG ready** when a test query returns at least one chunk with score > 0.5 (tune threshold in RAG agent).
- **CLI ready** when `oakley ask` returns answer-contract JSON to stdout.

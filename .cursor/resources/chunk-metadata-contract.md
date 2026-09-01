# Oakley Chunk Metadata Contract

Every chunk in `chunk_manifest.json` and Chroma metadata **must** include these fields.

## Required fields

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | string | Stable ID: `{source_type}:{content_hash}:{chunk_index}` |
| `chunk_index` | int | 0-based order within source document |
| `text` | string | Chunk body (manifest only; stored as Chroma `document`) |
| `source_file` | string | Basename, e.g. `Recorded-OAKWOOD-GLEN-....pdf` |
| `source_path` | string | Relative path from repo root, e.g. `hoa_docs/bylaws/foo.pdf` |
| `source_type` | enum | `hoa_bylaw` \| `county_regulation` |
| `document_title` | string | Human-readable title (see corpus-inventory.md) |
| `page_start` | int | 1-based start page |
| `page_end` | int | 1-based end page (inclusive) |
| `section_heading` | string | Nearest detected heading; empty string if none |
| `char_offset` | int | Character offset in extracted full-doc text |
| `content_hash` | string | SHA-256 hex of normalized full document text |
| `token_estimate` | int | Approximate token count for chunk text |
| `content_format` | enum | `pdf` \| `markdown` |
| `doc_category` | string | `bylaws`, `policies`, `deed_restrictions`, `faqs`, `county` |

## Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `context_doc_path` | string | Relative path to companion `.md` in same folder (PDF chunks only) |
| `context_doc_excerpt` | string | First ~500 chars of companion markdown (truncated for Chroma) |
| `parent_section` | string | Higher-level section if nested |
| `needs_ocr` | bool | Page had low extractable text density |

## source_type enum

| Value | Source roots |
|-------|--------------|
| `hoa_bylaw` | `hoa_docs/**` |
| `county_regulation` | `county_regulations/` |

## Manifest file shape

```json
{
  "manifest_id": "20260829-a1b2c3",
  "created_at": "2026-08-29T18:00:00Z",
  "ingest_version": "2",
  "previous_manifest_id": "20260828-deadbe",
  "source_files": [
    {
      "source_path": "hoa_docs/bylaws/Recorded-OAKWOOD-GLEN-....pdf",
      "content_hash": "...",
      "page_count": 42,
      "chunk_count": 87,
      "content_format": "pdf",
      "doc_category": "bylaws",
      "needs_ocr_pages": []
    }
  ],
  "chunks": [ /* array of chunk objects per required fields */ ],
  "stats": {
    "total_chunks": 150,
    "total_tokens_estimate": 120000,
    "by_source_type": {
      "hoa_bylaw": 120,
      "county_regulation": 30
    },
    "files_parsed": 5,
    "files_reused": 12,
    "files_moved": 0,
    "files_empty": 0,
    "chunk_delta": 154
  }
}
```

## Citation format

When citing a chunk in user-facing output:

```
[Document Title, p. N]
```

- Use `document_title` and `page_start` (or range `p. N–M` if `page_end` differs).
- Inline citations in answer prose; duplicate in structured `citations[]` array (see answer-contract.md).
- UI may show `doc_category` as a badge on citation cards.

## Chunking rules

1. **PDF:** Prefer splits at section boundaries (`Section`, `Article`, `ARTICLE`, numbered headings). Target ~800 tokens, 100-token overlap.
2. **Markdown:** Split on `#` / `##` / `###` headings; FAQ `Q:` blocks stay within section chunks. Synthetic `page_start=1`, `page_end=1`.
3. Do not split mid-sentence when avoidable.
4. Each chunk should be self-contained enough for retrieval (include section heading in text prefix when helpful).

## Validation

Ingestion agent must validate before handoff:

- All required fields present on every chunk
- `source_type` matches corpus root
- `page_start` <= `page_end`
- `chunk_id` unique within manifest
- `content_hash` consistent for all chunks from same source file

---
name: oakley-ingest
description: Extract, clean, and chunk HOA and county regulation PDFs for Oakley. Use when working on PDF parsing, chunk manifests, bylaws/ or county_regulations/ ingestion, or scripts/ingest.py.
---

# Oakley Ingest

## Scope

`src/oakley/ingest/`, `scripts/ingest.py`, `data/processed/`, source PDFs in `bylaws/`, `county_regulations/`.

## Responsibilities

1. Extract text from PDFs using PyMuPDF (`pymupdf`).
2. Clean extracted text (normalize whitespace, strip headers/footers where detectable).
3. Section-aware chunking per `.cursor/resources/chunk-metadata-contract.md`.
4. Write `data/processed/<manifest_id>/chunk_manifest.json` with stats.
5. Flag low text-density pages as `needs_ocr` in manifest stats (OCR out of MVP scope).

## Rules

- **Do not** embed vectors or write to Chroma in this skill's turn.
- **Do not** call Gemini generation; embedding is Vector Store's job.
- **Do not** invent metadata fields outside the chunk contract.
- Use `document_title` from `.cursor/resources/corpus-inventory.md` unless PDF cover provides a better title.
- Secrets: never open `.env`.

## Default parameters

| Parameter | Value |
|-----------|-------|
| target_tokens | 800 |
| overlap_tokens | 100 |
| min_chunk_chars | 100 |

## Downstream handoff triggers

| Change | Notify |
|--------|--------|
| New chunk metadata field | Vector Store, RAG, update chunk-metadata-contract |
| New source PDF | Update corpus-inventory.md, Vector Store, QA |
| Manifest schema version bump | Vector Store, RAG, CLI, QA |
| Extractor swap (e.g. add OCR) | Vector Store, QA |

## References

- `.cursor/resources/chunk-metadata-contract.md`
- `.cursor/resources/corpus-inventory.md`
- `.cursor/resources/pipeline-contract.md`

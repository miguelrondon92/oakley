---
name: oakley-qa
description: Verify Oakley ingest, indexing, and RAG answers with golden fixtures. Use when adding tests, regression checks, or validating citations against known document sections.
---

# Oakley QA

## Scope

`tests/`, `tests/fixtures/`, golden Q&A YAML/JSON.

## Responsibilities

1. Assert ingestion produces valid `chunk_manifest.json` per chunk-metadata-contract.
2. Assert all manifest chunk_ids exist in Chroma after index step.
3. Golden questions: expected `source_file`, `page_start`, `refused` flag.
4. Regression: citation format, no hallucinated section numbers when refused.
5. Optional integration test with mocked Gemini (unit) + smoke test with real API (manual/CI flag).

## Golden fixture shape

```yaml
# tests/fixtures/golden_questions.yaml
- question: "What is the ACC appeal process?"
  source_type_filter: hoa_bylaw
  expect_refused: false
  expect_citation:
    source_file: ACC-Denial-Letter-and-Appeal-Hearing-Policy_REAL-PROPERTY_2021.pdf
    page_start_min: 1
    page_start_max: 5
- question: "What is the federal tax code for HOAs?"
  expect_refused: true
  refusal_reason: no_relevant_chunks
```

## Rules

- Never run commands that print `.env` or API key values.
- Do not commit `.env`, fixtures with real keys, or handoffs containing credentials.
- Prefer mocking `GEMINI_API_KEY` in unit tests; live Gemini tests are opt-in only.
- QA failures should name the owning agent (Ingestion, Vector, RAG, CLI).

## Minimum MVP test count

5–10 golden questions covering:

- Oakwood Glen bylaws (architectural, pool, violations)
- Harris County regulations
- At least one cross-corpus question
- At least one out-of-scope refusal

## References

- `.cursor/resources/answer-contract.md`
- `.cursor/resources/chunk-metadata-contract.md`
- `.cursor/resources/corpus-inventory.md`

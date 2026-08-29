---
name: oakley-rag
description: Retrieve relevant Oakley regulation chunks and generate cited Gemini answers. Use when working on retrieval tuning, RAG prompts, citation formatting, or src/oakley/rag/.
---

# Oakley RAG

## Scope

`src/oakley/rag/`, prompt templates, answer formatting.

## Responsibilities

1. Embed user query (same model as corpus: `text-embedding-004`).
2. Retrieve top-K chunks from Vector Store with optional `source_type` filter.
3. Build prompt with chunk context and citation instructions.
4. Generate answer via Gemini (`GEMINI_MODEL` from config).
5. Format output per `.cursor/resources/answer-contract.md`.
6. Refuse when confidence is low — never hallucinate regulations.

## Rules

- **Always read current `GEMINI_MODEL` before generation** — never hardcode model strings.
- Stamp `provider_model` on every answer.
- Every factual claim needs a citation from retrieved chunks.
- Use inline `[Document Title, p. N]` in answer prose.
- **Do not** parse PDFs or write to Chroma directly when Vector Store module exists.
- Secrets: never open `.env`.

## Default retrieval params

| Parameter | Default |
|-----------|---------|
| top_k | 5 (env `OAKLEY_TOP_K`) |
| min_score | 0.45 |
| confidence high | max_score ≥ 0.75 |
| confidence medium | max_score ≥ 0.55 |

## Downstream handoff triggers

| Change | Notify |
|--------|--------|
| Answer JSON shape change | CLI, QA, update answer-contract |
| Prompt / refusal policy change | QA (update golden expectations) |
| Retrieval threshold change | QA |
| New filter dimensions | CLI (flags), Vector Store if index metadata needed |

## References

- `.cursor/resources/answer-contract.md`
- `.cursor/resources/pipeline-contract.md`
- `.cursor/resources/chunk-metadata-contract.md`

# Oakley Answer Contract

RAG and CLI layers must produce answers matching this shape.

## Answer JSON (stdout / API response)

```json
{
  "question": "Can I build a fence without ACC approval?",
  "answer": "According to the Oakwood Glen Bylaws [Oakwood Glen Bylaws, p. 12], architectural changes require ACC approval before construction begins.",
  "citations": [
    {
      "document_title": "Oakwood Glen Bylaws (Second Amended and Restated)",
      "source_file": "Recorded-OAKWOOD-GLEN-SECOND-AMENDED-AND-RESTATED-BYLAWS-03782964xC3D0.pdf",
      "source_type": "hoa_bylaw",
      "page_start": 12,
      "page_end": 12,
      "section_heading": "Article IV — Architectural Control",
      "chunk_id": "hoa_bylaw:abc123:14",
      "quote": "No improvement shall be commenced until..."
    }
  ],
  "retrieved_chunk_ids": ["hoa_bylaw:abc123:14", "hoa_bylaw:abc123:15"],
  "confidence": "high",
  "refused": false,
  "refusal_reason": null,
  "provider_model": "gemini-2.0-flash",
  "retrieval": {
    "top_k": 5,
    "filters": {},
    "max_score": 0.89
  }
}
```

## Field semantics

| Field | Required | Notes |
|-------|----------|-------|
| `question` | yes | Echo of user input |
| `answer` | yes* | Natural language; inline `[Document Title, p. N]` citations |
| `citations` | yes | Structured list; empty when refused |
| `retrieved_chunk_ids` | yes | All chunks passed to generator |
| `confidence` | yes | `high` \| `medium` \| `low` |
| `refused` | yes | `true` when cannot answer safely |
| `refusal_reason` | if refused | e.g. `"no_relevant_chunks"`, `"low_confidence"` |
| `provider_model` | yes | From `GEMINI_MODEL` at generation time |
| `retrieval` | yes | Debug metadata for QA |

*When `refused=true`, `answer` should explain why (no hallucinated rules).

## Confidence rules

| Level | Condition |
|-------|-----------|
| `high` | max retrieval score ≥ 0.75 and ≥ 1 citation directly supports answer |
| `medium` | max score ≥ 0.55 or partial support across chunks |
| `low` | max score < 0.55 |

When confidence is `low`, set `refused=true` and `refusal_reason="low_confidence"`.

## Refusal policy

**Do not invent regulations.** Refuse when:

- No chunks retrieved above minimum score threshold (default 0.45)
- Retrieved chunks contradict each other without resolution
- Question is outside corpus scope (federal law, unrelated jurisdictions)

Suggested refusal message template:

> I couldn't find a clear answer in the Oakwood Glen HOA bylaws or Harris County regulations provided. Try rephrasing, or specify whether you're asking about HOA rules or county regulations.

## Citation requirements

1. Every factual claim in `answer` must have at least one matching entry in `citations[]`.
2. `quote` should be a short verbatim excerpt (≤ 300 chars) from the chunk.
3. Prefer citing the most specific policy document over the general bylaws when both apply.

## CLI output modes

| Flag | Behavior |
|------|----------|
| (default) | Pretty-print answer text + Sources list |
| `--json` | Full answer-contract JSON to stdout |

## QA assertions

Golden tests should check:

- `refused` matches expectation
- At least one citation's `source_file` and `page_start` match fixture
- `provider_model` is non-empty
- No answer when `refused=true` contains fabricated section numbers

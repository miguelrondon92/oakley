---
name: oakley-pipeline-handoff
description: Produce a structured handoff packet so Oakley layer changes propagate from ingestion through vector store, RAG, CLI, and QA. Use after finishing work in any pipeline layer or when orchestrating multi-agent collaboration.
---

# Oakley Pipeline Handoff

## Instructions

After completing a layer change (or when blocking on another owner):

1. Identify **from** and **to** owners using `.cursor/resources/agent-roster.md`.
2. Diff against `.cursor/resources/pipeline-contract.md` — update the contract if the data shape changed.
3. Write a handoff packet (chat summary and optionally `.cursor/handoffs/<yyyy-mm-dd>-<slug>.md`):

```markdown
## Handoff: <FROM> → <TO>
Date: <ISO date>
Status: ready | blocked

### Change
<1-5 bullets>

### Contract delta
- Fields added: …
- Fields changed: …
- Fields removed: …
- Re-index required: yes/no

### Answer / citation impact
none | retrieval changed | citation format changed

### Next owner actions
- [ ] …

### Suggested tests
- [ ] …
```

4. If multiple downstream owners, emit **one packet per owner** or a single packet with clear sections.
5. Orchestrator must not skip QA when user-visible behavior changed.

## Ordering reminder

```
Ingestion → Vector Store → RAG → CLI → QA
```

If Vector Store is blocked on new metadata fields, do not continue RAG work that assumes the new shape.

## Contract files to update when shape changes

| Layer | Likely contract file |
|-------|---------------------|
| Ingestion | `chunk-metadata-contract.md`, `corpus-inventory.md` |
| Vector Store | `pipeline-contract.md` (Chroma shape) |
| RAG | `answer-contract.md` |
| CLI | `answer-contract.md` (output flags) |

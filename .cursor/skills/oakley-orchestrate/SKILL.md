---
name: oakley-orchestrate
description: Coordinate multi-layer Oakley features across ingestion, vector store, RAG, CLI, and QA. Use when a change spans PDF processing through query UI, when subagents must collaborate, or when the user asks to implement an end-to-end Oakley feature.
---

# Oakley Orchestrate

## When to use

Any task that touches **two or more** of: Ingestion, Vector Store, RAG, CLI, QA (API/Web in Phase 2).

## Protocol

1. Read `AGENTS.md` and `.cursor/resources/pipeline-contract.md`.
2. Write a one-paragraph plan naming owners in order.
3. Execute layers **in order** (skip untouched layers):

```
Ingestion → Vector Store → RAG → CLI → QA
```

When work involves `GEMINI_MODEL`, quota, or `.env.example`, include **Gemini Ops** after Vector Store or RAG writers.

Phase 2: insert **API/Web** before QA.

4. After each layer, run skill `oakley-pipeline-handoff` (or write the packet yourself).
5. Do not mark complete until QA confirms golden answers and citations.

## Subagent spawning

When using Task/subagents, give each:

- Role name from `.cursor/resources/agent-roster.md`
- Exact file globs
- The prior handoff packet
- Explicit **secrets ban**: user inputs keys in local `.env` only; never read `.env`, never print/commit/log keys, never ask user to paste keys into chat

Example sequence for "implement full RAG pipeline":

1. Ingestion → chunk manifest in `data/processed/`
2. Vector Store → embed + Chroma index
3. RAG → retrieval + prompts + answer formatter
4. CLI → `oakley ingest` / `oakley ask`
5. QA → golden fixtures

Example Task prompt:

> Role: Oakley Ingestion Agent. Read `.cursor/resources/chunk-metadata-contract.md`. Build `scripts/ingest.py` that writes manifests to `data/processed/`. Do not touch Chroma or Gemini generation. Emit handoff to Vector Store agent.

## Conflict resolution

- Metadata disputes → Ingestion wins on chunk fields; Vector Store wins on Chroma storage constraints
- Citation format → RAG wins on semantics; CLI wins on presentation flags only
- Rate limits → Gemini Ops owns quota narrative; RAG must tolerate 429 with backoff
- `GEMINI_MODEL` constant → Gemini Ops; stamping on answers → RAG

## Secrets

Never read `.env` or keys. Never commit secret files or live API key strings. Orchestrator must not ask subagents to dump env or paste keys into chat. User inputs `GEMINI_API_KEY` in local `.env` only. See `.cursor/resources/secrets-policy.md`.

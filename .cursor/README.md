# Oakley Cursor Agentic System

Project-local Cursor configuration for multi-agent Oakley development.

Human-facing overview: [`../README.md`](../README.md). Pipeline rules for agents: [`../AGENTS.md`](../AGENTS.md).

## Layout

| Path | Purpose |
|------|---------|
| `hooks.json` | Hook registration (secrets + pipeline) |
| `hooks/` | Executable hook scripts |
| `rules/` | Always-on + path-scoped agent rules |
| `skills/` | Domain skills for orchestrator and specialists |
| `resources/` | Shared contracts (pipeline, chunks, answers, corpus) |
| `handoffs/` | Written handoff packets between agents |

## Enabling

Cursor loads project hooks from `.cursor/hooks.json` automatically. Confirm in **Cursor Settings → Hooks**. Restart Cursor if hooks do not appear after the first add.

Skills under `.cursor/skills/*/SKILL.md` are project skills. Rules under `.cursor/rules/*.mdc` apply per frontmatter.

## Security model

Fail-closed hooks block:

- Reading `.env` and private key / credential files
- Shell commands that dump env, read secret files, or `git add .env`
- Writes containing private key PEM material or live `AIza…` API keys (`.env.example` placeholders allowed)
- Prompts that ask to reveal secrets or paste keys into chat (best-effort)

Allowed references: `.env.example` only. **Only the human user edits local `.env`.**

Full policy: `resources/secrets-policy.md`

Optional git safety: user runs `git config core.hooksPath .githooks` (see `.githooks/README.md`).

## Orchestration

Use skill **oakley-orchestrate** for cross-layer work. Subagent completion triggers a pipeline follow-up reminder via `subagentStop`.

Shared contracts under `resources/`:

- `pipeline-contract.md` — PDF → manifest → Chroma → answer flow
- `chunk-metadata-contract.md` — required chunk fields and citation format
- `answer-contract.md` — RAG output shape and refusal policy
- `corpus-inventory.md` — source PDF catalog
- `agent-roster.md` — owners and file globs
- `secrets-policy.md` — user-only secrets; no agent access to keys

After ingest/RAG/CLI changes: run golden QA fixtures before closing a handoff.

## Agent skills

| Skill | Owner |
|-------|-------|
| `oakley-orchestrate` | Orchestrator |
| `oakley-ingest` | Ingestion |
| `oakley-vector` | Vector Store |
| `oakley-rag` | RAG |
| `oakley-gemini-ops` | Gemini Ops |
| `oakley-cli` | CLI / API |
| `oakley-pipeline-handoff` | All layers |
| `oakley-qa` | QA |

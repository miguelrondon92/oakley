#!/usr/bin/env bash
set -euo pipefail

# sessionStart: inject agentic architecture context (no secrets).
cat <<'EOF'
{
  "additional_context": "Oakley agentic mode active. Roster: Orchestrator, Ingestion, Vector Store, RAG, Gemini Ops, CLI/API, QA. Pipeline: Ingestion -> Vector Store -> RAG -> CLI -> QA. Contracts: .cursor/resources/pipeline-contract.md, chunk-metadata-contract.md, answer-contract.md, corpus-inventory.md, secrets-policy.md, agent-roster.md. Skills: oakley-orchestrate, oakley-ingest, oakley-vector, oakley-rag, oakley-gemini-ops, oakley-cli, oakley-pipeline-handoff, oakley-qa. SECRETS (non-negotiable): only the human user may input or view secret values in local .env. Agents never read .env, never print/commit/log API keys, never push secrets to GitHub, never ask user to paste keys into chat. Use .env.example for variable names only. After layer changes, emit a handoff packet (no secrets in handoffs)."
}
EOF

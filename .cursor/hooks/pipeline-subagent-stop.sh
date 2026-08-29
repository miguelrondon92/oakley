#!/usr/bin/env bash
set -euo pipefail

input="$(cat)"
summary="$(echo "$input" | jq -r '.summary // .result // .message // empty' | head -c 500)"

followup="Oakley pipeline check: if this subagent changed ingestion manifests, Chroma schema, RAG answers, or CLI output, run skill oakley-pipeline-handoff and continue the next owner in order (Ingestion -> Vector Store -> RAG -> CLI -> QA). SECRETS: never read .env, never print or commit API keys, user inputs secrets locally only — pass this ban to any further subagents. Prior summary: ${summary:-"(none)"}"

jq -n --arg m "$followup" '{followup_message:$m}'

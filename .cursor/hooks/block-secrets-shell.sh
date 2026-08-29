#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$DIR/_common.sh"

input="$(cat)"
cmd="$(echo "$input" | jq -r '.command // .tool_input.command // empty')"

if [[ -z "$cmd" ]]; then
  allow_json
  exit 0
fi

if command_touches_secrets "$cmd"; then
  deny_json \
    "Blocked: shell command may expose secrets or private keys." \
    "Shell command denied by Oakley secrets hook. User inputs secrets in local .env only. Do not cat .env, printenv, git add .env, or dump API keys."
  exit 0
fi

allow_json
exit 0

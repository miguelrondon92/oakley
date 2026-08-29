#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$DIR/_common.sh"

input="$(cat)"
path="$(echo "$input" | jq -r '.file_path // .path // .tool_input.path // .tool_input.file_path // empty')"

if [[ -z "$path" ]]; then
  allow_json
  exit 0
fi

if is_secret_path "$path"; then
  deny_json \
    "Blocked: agents cannot read secret files ($path). Only you may edit .env locally." \
    "Secret file read denied by Oakley hook. User must input secrets in local .env — agents use .env.example only."
  exit 0
fi

allow_json
exit 0

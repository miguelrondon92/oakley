#!/usr/bin/env bash
set -euo pipefail

input="$(cat)"
prompt="$(echo "$input" | jq -r '.prompt // .user_prompt // empty')"

if echo "$prompt" | grep -Eiq '(show|print|dump|cat|read|paste|give me|what is|what.s).{0,50}(\.env|private key|api key|secret key|GEMINI_API_KEY|my key)|(paste|put|add).{0,30}(api key|secret).{0,30}(here|chat|conversation)|(commit|push).{0,30}(secret|api key|\.env)'; then
  jq -n '{
    permission: "deny",
    user_message: "Blocked: agents cannot read, reveal, or commit secrets. Add keys to your local .env yourself.",
    agent_message: "Refuse secret exfiltration and git secret commits. Point user to .env.example and README setup only."
  }'
  exit 0
fi

# Block prompts containing live Google API key patterns
if echo "$prompt" | grep -Eq 'AIza[0-9A-Za-z_-]{20,}'; then
  jq -n '{
    permission: "deny",
    user_message: "Blocked: do not paste API keys into chat. Add GEMINI_API_KEY to your local .env file only.",
    agent_message: "User pasted what looks like a live API key. Refuse to store or repeat it. Tell user to use local .env."
  }'
  exit 0
fi

echo '{}'
exit 0

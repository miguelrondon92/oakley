#!/usr/bin/env bash
# Shared helpers for Oakley Cursor hooks (source from other scripts).

is_secret_path() {
  local path="$1"
  path="${path//\\/\/}"
  local base
  base="$(basename "$path")"

  case "$path" in
    *.env|*/.env|*/.env.*|.env|.env.*)
      case "$base" in
        .env.example|*.example|*.template) return 1 ;;
      esac
      return 0
      ;;
  esac

  case "$base" in
    .env|.env.*|*.pem|*.key|id_rsa|id_rsa.*|*credentials*.json|*firebase-adminsdk*.json|serviceAccount*.json|secrets.json|secrets.yaml|secrets.yml)
      case "$base" in
        .env.example|*.example|*.template) return 1 ;;
      esac
      return 0
      ;;
  esac

  return 1
}

# Detect live API key material (Google Gemini keys often start with AIza)
contains_live_api_key() {
  local text="$1"
  # Google API key pattern
  if echo "$text" | grep -Eq 'AIza[0-9A-Za-z_-]{20,}'; then
    # Allow obvious placeholders in .env.example-style content
    if echo "$text" | grep -Eq 'AIza[0-9A-Za-z_-]*(your_|placeholder|example|xxx|REPLACE|CHANGEME)'; then
      return 1
    fi
    return 0
  fi
  # Generic assignment of non-placeholder secret values
  if echo "$text" | grep -Eiq 'GEMINI_API_KEY[[:space:]]*=[[:space:]]*[^[:space:]#]+' \
    && ! echo "$text" | grep -Eiq 'GEMINI_API_KEY[[:space:]]*=[[:space:]]*(your_|placeholder|example|<|xxx|REPLACE|CHANGEME|\*\*)'; then
    return 0
  fi
  return 1
}

command_touches_secrets() {
  local cmd="$1"
  if echo "$cmd" | grep -Eiq '(cat|less|more|head|tail|bat|hexdump|xxd|nl|type|Get-Content)\>.*(\.env|\.pem|\.key|id_rsa|credentials\.json|firebase-adminsdk|serviceAccount|secrets\.(json|ya?ml))'; then
    return 0
  fi
  if echo "$cmd" | grep -Eiq '(^|[;&|[:space:]])(printenv|env)([|;[:space:]]|$)'; then
    return 0
  fi
  if echo "$cmd" | grep -Eiq '(echo|printf|print|Write-Output).{0,20}(GEMINI_API_KEY|SECRET_KEY|_API_KEY)'; then
    return 0
  fi
  if echo "$cmd" | grep -Eiq 'export[[:space:]]+[A-Za-z0-9_]*(KEY|PASSWORD|SECRET|TOKEN)='; then
    return 0
  fi
  if echo "$cmd" | grep -Eiq 'base64\>.*\.(env|pem|key)|openssl[[:space:]]+(rsa|ec)|ssh-keygen.*-y'; then
    return 0
  fi
  if echo "$cmd" | grep -Eiq 'python[0-9.]*[^|;]*(os\.environ|getenv|load_dotenv).{0,80}(print|pprint|log|debug)'; then
    return 0
  fi
  # Git: staging or committing secret files
  if echo "$cmd" | grep -Eiq 'git[[:space:]]+add(\s|$).{0,120}\.env'; then
    return 0
  fi
  if echo "$cmd" | grep -Eiq 'git[[:space:]]+add(\s|$).{0,120}(\.pem|\.key|credentials\.json)'; then
    return 0
  fi
  if echo "$cmd" | grep -Eiq 'git[[:space:]]+commit.{0,200}(GEMINI_API_KEY|AIza[0-9A-Za-z_-]{20,})'; then
    return 0
  fi
  if echo "$cmd" | grep -Eiq 'git[[:space:]]+(show|diff|log).{0,40}\.env'; then
    return 0
  fi
  return 1
}

deny_json() {
  local user_msg="$1"
  local agent_msg="$2"
  jq -n \
    --arg u "$user_msg" \
    --arg a "$agent_msg" \
    '{permission:"deny",user_message:$u,agent_message:$a}'
}

allow_json() {
  echo '{"permission":"allow"}'
}

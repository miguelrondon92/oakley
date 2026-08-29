# Oakley Secrets Policy

**Non-negotiable.** Applies to every agent, subagent, hook, skill, commit, log line, and handoff.

## Core rule

**Only the human user may create, view, or edit secret values.** Agents never read, write, print, commit, log, or transmit API keys, passwords, tokens, or private keys.

## User-only setup

1. User copies [`.env.example`](../../.env.example) to `.env` locally (never committed).
2. User pastes their own `GEMINI_API_KEY` and any other secrets into `.env`.
3. User runs `oakley ingest` / `oakley ask` in their own terminal where env is loaded.
4. Agents document **variable names** only; they never fill in real key values.

## Blocked for agents

| Action | Examples |
|--------|----------|
| Read secret files | `.env`, `.env.local`, `*.pem`, `*.key`, `*credentials*.json` |
| Shell dumps | `cat .env`, `printenv`, `env`, `echo $GEMINI_API_KEY` |
| Code that exfiltrates | `os.environ["GEMINI_API_KEY"]` in logs, `load_dotenv` + print |
| Write real keys | Pasting a live `AIza…` key into any tracked file |
| Git | `git add .env`, committing secret-bearing files or key strings |
| GitHub | Pushing secrets; agents must refuse to commit if diff contains key material |
| Prompts / handoffs | Asking user to paste key into chat; storing keys in handoff markdown |
| QA / debug | Tests that print env; scripts that echo configured key length is OK, value is not |

## Allowed for agents

- [`.env.example`](../../.env.example) (placeholders only)
- Referencing names: `GEMINI_API_KEY`, `GEMINI_MODEL`, `CHROMA_PERSIST_DIR`
- Instructions: "Copy `.env.example` to `.env` and add your Gemini API key"
- Runtime code that reads env **without logging values** (e.g. `os.getenv("GEMINI_API_KEY")` passed to SDK)
- Quota scripts that report **configured: yes/no** without printing the key

## Git / GitHub

- `.env` and secret patterns are in [`.gitignore`](../../.gitignore).
- Optional [`.githooks/pre-commit`](../../.githooks/pre-commit) blocks accidental secret commits if user enables hooks.
- Before any commit, agents must verify staged files exclude `.env`, `*.pem`, `*.key`, and files containing `AIza` API key patterns.
- If user asks to commit and secrets might be present, **stop and warn** — do not proceed.

## Logging and answers

- Never log `GEMINI_API_KEY` or full Authorization headers.
- Error messages: "GEMINI_API_KEY not set" — not the missing value.
- RAG/CLI output must not include env vars.

## Subagents

Orchestrator **must** pass secrets ban to every spawned subagent. Subagents inherit the same blocks as the parent.

## If blocked or asked to reveal secrets

1. Refuse clearly.
2. Point user to `.env.example` and local setup in README.
3. Do not suggest workarounds (alternate read tools, base64 decode, etc.).

## Enforcement layers

1. Cursor hooks (read, shell, write, prompt)
2. Always-on rules (`01-secrets-never.mdc`, `03-secrets-git-and-logs.mdc`)
3. `AGENTS.md` and every agent skill
4. `.gitignore` + optional pre-commit hook

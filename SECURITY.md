# Security Policy

Oakley is designed for **local, single-user use**. The web chat binds to `127.0.0.1` by default and has no authentication.

## Secrets

- **Never commit** `.env`, API keys, private keys, or credential JSON files.
- Copy [`.env.example`](.env.example) to `.env` locally and add your own `GEMINI_API_KEY`.
- Only [`.env.example`](.env.example) (placeholders) belongs in the repository.
- If you fork this repo, treat your `.env` as private and rotate keys if they are ever exposed.

## Local-only deployment

`oakley serve` is intended for your machine only. Do **not** expose it to the internet without:

- Authentication and authorization
- Rate limiting
- HTTPS termination
- Network firewall rules

An unauthenticated public instance would allow anyone to use your Gemini API quota and read/write local conversation data.

## Reporting a security issue

If you find a vulnerability or accidentally committed a secret:

1. **Do not** open a public GitHub issue with key material or exploit details.
2. If a Gemini API key was committed: **rotate the key immediately** in [Google AI Studio](https://aistudio.google.com/apikey), regardless of whether the commit was reverted.
3. Open a private security advisory on GitHub (Security → Advisories → New draft) or contact the maintainer directly.

## Supported versions

This is a personal/local project with no formal release cadence. Security fixes apply to the `main` branch.

## What we scan for

The optional pre-commit hook (`.githooks/pre-commit`) blocks:

- Staged `.env` and key files
- Live Google API key patterns (`AIza…`)
- Non-placeholder `GEMINI_API_KEY=` assignments in diffs

Enable locally:

```bash
git config core.hooksPath .githooks
```

After making the repo public, enable **Secret scanning** under GitHub repository Settings → Code security.

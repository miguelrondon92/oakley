# Oakley

AI assistant for **local governing-entity regulations** — starting with **Oakwood Glen HOA** (Harris County, TX) and **Harris County** regulations.

Ask questions about bylaws, policies, and county rules; get answers **with citations** from the source PDFs.

## Corpus

| Directory | Contents |
|-----------|----------|
| [`bylaws/`](bylaws/) | 8 Oakwood Glen HOA PDFs (bylaws + policies) |
| [`county_regulations/`](county_regulations/) | 2 Harris County regulation PDFs |

Full catalog: [`.cursor/resources/corpus-inventory.md`](.cursor/resources/corpus-inventory.md)

## Architecture (planned)

```
PDFs → extract & chunk → Chroma (Gemini embeddings) → RAG (Gemini) → CLI → web chat
```

| Layer | Technology |
|-------|------------|
| Extraction | PyMuPDF |
| Embeddings | Gemini `text-embedding-004` |
| Vector store | Chroma (local, `data/chroma/`) |
| Generation | Gemini Flash (`GEMINI_MODEL`) |
| Interface | CLI first, then web chat |

## Agentic development

This project uses a multi-agent Cursor setup. Before implementing features, read [`AGENTS.md`](AGENTS.md).

- **Skills:** `.cursor/skills/oakley-*`
- **Contracts:** `.cursor/resources/`
- **Handoffs:** `.cursor/handoffs/`

To build the pipeline, tell the agent: *"Implement Oakley ingest"* — it will follow the Ingestion → Vector → RAG → CLI → QA sequence.

## Setup (once app code exists)

**Secrets are yours alone.** Agents never read or fill in API keys. You configure them locally:

1. Copy `.env.example` to `.env` (`.env` is gitignored — never pushed to GitHub)
2. Paste your Gemini API key into `.env` as `GEMINI_API_KEY` — do not paste keys into Cursor chat
3. Optional: enable the pre-commit hook to block accidental secret commits:
   ```bash
   git config core.hooksPath .githooks
   ```
4. `pip install -e .` (when `pyproject.toml` exists)
5. Run in **your terminal** (where `.env` is loaded): `oakley ingest`, then `oakley ask "…"`

See [`.cursor/resources/secrets-policy.md`](.cursor/resources/secrets-policy.md) for the full policy agents follow.

## Status

**Infrastructure only** — agent coordination layer is in place; Python RAG code not yet implemented.

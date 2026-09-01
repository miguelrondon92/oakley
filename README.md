# Oakley

AI assistant for **local governing-entity regulations** — starting with **Oakwood Glen HOA** (Harris County, TX) and **Harris County** regulations.

Ask questions about bylaws, policies, and county rules; get answers **with citations** from the source documents (PDFs and markdown).

## Corpus

```
hoa_docs/
├── bylaws/                          # 8 HOA PDFs (moved from legacy bylaws/)
├── policies/                        # 14 policy PDFs
├── policies/deed_restrictions/      # 3 PDFs + deed_restrictions.md
└── faqs/faqs.md                     # FAQ markdown
county_regulations/                  # 2 Harris County PDFs
```

| Directory | Contents |
|-----------|----------|
| [`hoa_docs/bylaws/`](hoa_docs/bylaws/) | 8 Oakwood Glen HOA bylaws PDFs |
| [`hoa_docs/policies/`](hoa_docs/policies/) | 14 association policy PDFs |
| [`hoa_docs/policies/deed_restrictions/`](hoa_docs/policies/deed_restrictions/) | Deed restriction PDFs + overview markdown |
| [`hoa_docs/faqs/`](hoa_docs/faqs/) | FAQ markdown |
| [`county_regulations/`](county_regulations/) | 2 Harris County regulation PDFs |

## Setup

**Secrets are yours alone** — copy [`.env.example`](.env.example) to `.env` and add your `GEMINI_API_KEY` locally. Never commit `.env`.

```bash
cd oakley
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python scripts/fix_venv.py   # macOS: Python 3.12 skips hidden .pth files from pip

# Optional: block accidental secret commits
git config core.hooksPath .githooks
```

## Commands

| Command | Description |
|---------|-------------|
| `oakley status` | Corpus, manifest, and Chroma stats |
| `oakley parse` | Incremental parse → chunk manifest (reuses unchanged files) |
| `oakley parse --source hoa` | HOA docs only (`hoa_docs/**`; `--source bylaws` is an alias) |
| `oakley parse --source county` | County PDFs only |
| `oakley parse --force` | Force re-parse all files |
| `oakley parse --dry-run` | Report new/reused/changed counts without writing |
| `oakley index` | Embed only new/changed chunks → Chroma (prunes orphans by default) |
| `oakley ingest` | `parse` + `index` |
| `oakley ask "…"` | RAG question with citations |
| `oakley ask "…" --json` | Full answer JSON |
| `oakley ask "…" --source-type hoa_bylaw` | Filter to HOA docs |
| `oakley serve` | Web chat UI at http://127.0.0.1:8080 |
| `oakley serve --port 9000` | Custom port |
| `oakley clean manifest -y` | Wipe `data/processed/` |
| `oakley clean index -y` | Wipe `data/chroma/` |
| `oakley clean all -y` | Full reset |

### Idempotent reset cheat sheet

| Goal | Command |
|------|---------|
| Re-chunk everything | `oakley clean manifest -y && oakley parse --force` |
| Re-embed only | `oakley clean index -y && oakley index` |
| Ingest new/changed files only | `oakley parse && oakley index` |
| Full pipeline reset | `oakley clean all -y && oakley ingest --force` |
| Check state | `oakley status` |

## Web chat

```bash
oakley serve
# Open http://127.0.0.1:8080
```

Features:

- **Conversation sidebar** — resume past threads (stored in `data/oakley.db`)
- **Source toggle** — All / HOA / County per conversation
- **Citation cards** — document, page, category badge, and quote under each answer
- **Follow-up questions** — prior turns included in the answer prompt

Run `oakley ingest` first if the UI reports no indexed documents.

## Architecture

```
PDFs + Markdown → incremental manifest → Chroma → RAG → CLI / Web chat
```

| Layer | Technology |
|-------|------------|
| Extraction | PyMuPDF (PDF), heading-based chunking (markdown) |
| Embeddings | Gemini `gemini-embedding-001` |
| Vector store | Chroma (local, `data/chroma/`) |
| Generation | Gemini (`GEMINI_MODEL`) |
| Conversations | SQLite (`data/oakley.db`) |
| Interface | CLI + web chat (`oakley serve`) |

## Tests

```bash
pytest                          # unit tests only
pytest -m integration           # requires GEMINI_API_KEY in your .env
```

## Agentic development

Multi-agent Cursor setup: [`AGENTS.md`](AGENTS.md)

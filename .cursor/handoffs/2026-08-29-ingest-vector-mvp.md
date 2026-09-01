## Handoff: Ingestion → Vector Store
Date: 2026-08-29
Status: ready

### Change
- Implemented `oakley parse` producing manifest `20260829-68a8ca` with 258 chunks from 10 PDFs
- Chunk metadata matches chunk-metadata-contract (all required fields)
- Embedding model: `models/gemini-embedding-001` (text-embedding-004 unavailable on current API key)

### Contract delta
- Fields added: none
- Fields changed: embedding model env `OAKLEY_EMBEDDING_MODEL` documented in `.env.example`
- Fields removed: none
- Re-index required: yes (completed — 258 vectors in Chroma)

### Answer / citation impact
none

### Next owner actions
- [x] Index manifest into Chroma
- [ ] Tune RAG retrieval thresholds if ask quality needs improvement
- [ ] Add golden integration tests to CI with secret from env

### Suggested tests
- [x] `oakley index` → 258 vectors
- [x] `oakley ask "ACC appeal process"` returns ACC policy citation
- [ ] `pytest -m integration` golden fixtures

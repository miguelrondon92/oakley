"""Chroma vector store operations."""

from __future__ import annotations

from typing import Any

import chromadb

from oakley.config import COLLECTION_NAME, get_settings, resolve_path
from oakley.ingest.manifest import Manifest, load_previous_manifest
from oakley.vector.embedder import embed_texts


def _chroma_client():
    settings = get_settings()
    persist = resolve_path(settings.chroma_persist_dir, settings)
    persist.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist))


def get_collection():
    client = _chroma_client()
    return client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def collection_count() -> int | None:
    try:
        col = get_collection()
        return col.count()
    except Exception:
        return None


def _chunk_metadata(chunk: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Flat metadata for Chroma (no text field)."""
    meta: dict[str, str | int | float | bool] = {
        "chunk_index": int(chunk["chunk_index"]),
        "source_file": str(chunk["source_file"]),
        "source_path": str(chunk["source_path"]),
        "source_type": str(chunk["source_type"]),
        "document_title": str(chunk["document_title"]),
        "page_start": int(chunk["page_start"]),
        "page_end": int(chunk["page_end"]),
        "section_heading": str(chunk.get("section_heading", "")),
        "char_offset": int(chunk["char_offset"]),
        "content_hash": str(chunk["content_hash"]),
        "token_estimate": int(chunk["token_estimate"]),
        "content_format": str(chunk.get("content_format", "pdf")),
        "doc_category": str(chunk.get("doc_category", "")),
    }
    if chunk.get("context_doc_path"):
        meta["context_doc_path"] = str(chunk["context_doc_path"])
    if chunk.get("context_doc_excerpt"):
        meta["context_doc_excerpt"] = str(chunk["context_doc_excerpt"])[:500]
    return meta


def _metadata_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return _chunk_metadata(a) == _chunk_metadata(b)


def _chunks_needing_work(
    manifest: Manifest,
    previous: Manifest | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Return (embed_chunks, metadata_only_chunks, skipped_count)."""
    if previous is None:
        return manifest.chunks, [], 0

    prev_by_id = {c["chunk_id"]: c for c in previous.chunks}
    embed: list[dict[str, Any]] = []
    metadata_only: list[dict[str, Any]] = []
    skipped = 0

    for chunk in manifest.chunks:
        cid = chunk["chunk_id"]
        prev = prev_by_id.get(cid)
        if prev is None:
            embed.append(chunk)
        elif prev.get("text") != chunk.get("text") or prev.get("content_hash") != chunk.get("content_hash"):
            embed.append(chunk)
        elif not _metadata_equal(prev, chunk):
            metadata_only.append(chunk)
        else:
            skipped += 1

    return embed, metadata_only, skipped


def index_manifest(manifest: Manifest, batch_size: int = 5, prune_orphans: bool = True) -> dict[str, int]:
    col = get_collection()
    previous = load_previous_manifest(manifest)
    embed_chunks, metadata_only, skipped = _chunks_needing_work(manifest, previous)

    indexed = 0
    files_embedded = len({c["source_path"] for c in embed_chunks})
    files_skipped = len({c["source_path"] for c in manifest.chunks}) - files_embedded

    for batch_start in range(0, len(embed_chunks), batch_size):
        batch = embed_chunks[batch_start : batch_start + batch_size]
        batch_ids = [c["chunk_id"] for c in batch]
        batch_docs = [c["text"] for c in batch]
        batch_meta = [_chunk_metadata(c) for c in batch]
        embeddings = embed_texts(batch_docs, batch_size=batch_size)
        col.upsert(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_meta,
            embeddings=embeddings,
        )
        indexed += len(batch_ids)

    if metadata_only:
        existing = col.get(
            ids=[c["chunk_id"] for c in metadata_only],
            include=["embeddings"],
        )
        emb_map: dict[str, list[float]] = {}
        raw_embs = existing.get("embeddings")
        ids_list = existing.get("ids") or []
        for i, cid in enumerate(ids_list):
            emb = None
            if raw_embs is not None:
                try:
                    emb = raw_embs[i]
                except (IndexError, TypeError, KeyError):
                    emb = None
            if emb is not None:
                emb_map[cid] = list(emb) if hasattr(emb, "__iter__") and not isinstance(emb, str) else emb

        for batch_start in range(0, len(metadata_only), batch_size):
            batch = metadata_only[batch_start : batch_start + batch_size]
            batch_ids = [c["chunk_id"] for c in batch]
            batch_docs = [c["text"] for c in batch]
            batch_meta = [_chunk_metadata(c) for c in batch]
            embeddings = []
            need_embed_indices: list[int] = []
            need_embed_texts: list[str] = []
            for i, cid in enumerate(batch_ids):
                if cid in emb_map:
                    embeddings.append(emb_map[cid])
                else:
                    embeddings.append(None)
                    need_embed_indices.append(i)
                    need_embed_texts.append(batch_docs[i])
            if need_embed_texts:
                new_embs = embed_texts(need_embed_texts, batch_size=batch_size)
                for idx, emb in zip(need_embed_indices, new_embs):
                    embeddings[idx] = emb
            col.upsert(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta,
                embeddings=embeddings,
            )
            indexed += len(batch_ids)

    ids = [c["chunk_id"] for c in manifest.chunks]
    pruned = 0
    if prune_orphans:
        existing = col.get(include=[])
        existing_ids = set(existing.get("ids") or [])
        manifest_ids = set(ids)
        orphan_ids = list(existing_ids - manifest_ids)
        if orphan_ids:
            col.delete(ids=orphan_ids)
            pruned = len(orphan_ids)

    return {
        "indexed": indexed,
        "skipped": skipped,
        "pruned": pruned,
        "files_embedded": files_embedded,
        "files_skipped": max(files_skipped, 0),
        "total_in_collection": col.count(),
    }


def search(
    query_embedding: list[float],
    top_k: int,
    source_type: str | None = None,
) -> list[dict[str, Any]]:
    col = get_collection()
    where = {"source_type": source_type} if source_type else None
    kwargs: dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    results = col.query(**kwargs)
    chunks: list[dict[str, Any]] = []
    if not results["ids"] or not results["ids"][0]:
        return chunks

    for idx, chunk_id in enumerate(results["ids"][0]):
        distance = results["distances"][0][idx] if results.get("distances") else 1.0
        score = max(0.0, 1.0 - distance)
        meta = results["metadatas"][0][idx] or {}
        text = results["documents"][0][idx] or ""
        chunks.append(
            {
                "chunk_id": chunk_id,
                "text": text,
                "score": score,
                **meta,
            }
        )
    return chunks


def clean_index() -> bool:
    settings = get_settings()
    persist = resolve_path(settings.chroma_persist_dir, settings)
    if not persist.exists():
        return False
    import shutil

    shutil.rmtree(persist)
    return True

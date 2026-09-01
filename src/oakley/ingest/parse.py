"""Orchestrate corpus parsing into chunk manifests (incremental per file)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from oakley.config import DOCUMENT_TITLES, INGEST_VERSION, get_settings
from oakley.ingest.chunk import chunk_document
from oakley.ingest.corpus import CorpusFile, collect_corpus_files, count_corpus_files
from oakley.ingest.extract import extract_pdf
from oakley.ingest.manifest import (
    Manifest,
    SourceFileRecord,
    content_hash,
    find_by_content_hash,
    load_latest_manifest,
    make_chunk_id,
    make_manifest_id,
    write_manifest,
)
from oakley.ingest.markdown import (
    chunk_markdown,
    extract_markdown,
    sidecar_context_for_dir,
)


@dataclass
class ParseResult:
    manifest: Manifest | None
    skipped: bool
    message: str
    dry_run_counts: dict[str, int] | None = None


def _document_title(corpus_file: CorpusFile) -> str:
    basename = corpus_file.path.name
    return DOCUMENT_TITLES.get(basename, basename.rsplit(".", 1)[0].replace("-", " "))


def _rewrite_chunk_paths(
    chunks: list[dict],
    *,
    source_path: str,
    source_file: str,
    doc_category: str,
    content_format: str,
    context_doc_path: str | None = None,
    context_doc_excerpt: str | None = None,
) -> list[dict]:
    updated: list[dict] = []
    for ch in chunks:
        new_ch = dict(ch)
        new_ch["source_path"] = source_path
        new_ch["source_file"] = source_file
        new_ch["doc_category"] = doc_category
        new_ch["content_format"] = content_format
        if context_doc_path:
            new_ch["context_doc_path"] = context_doc_path
        elif "context_doc_path" in new_ch:
            new_ch.pop("context_doc_path", None)
        if context_doc_excerpt:
            new_ch["context_doc_excerpt"] = context_doc_excerpt
        elif "context_doc_excerpt" in new_ch:
            new_ch.pop("context_doc_excerpt", None)
        updated.append(new_ch)
    return updated


def _build_chunks_from_pdf(
    corpus_file: CorpusFile,
    *,
    context_doc_path: str | None = None,
    context_doc_excerpt: str | None = None,
    disambiguate: bool = False,
) -> tuple[list[dict], SourceFileRecord]:
    extracted = extract_pdf(corpus_file.path, corpus_file.source_path)
    doc_hash = content_hash(extracted.full_text)
    page_segments = [(p.page_num, p.text) for p in extracted.pages if p.text]
    text_chunks = chunk_document(extracted.full_text, page_segments)
    document_title = _document_title(corpus_file)
    basename = corpus_file.path.name

    chunks: list[dict] = []
    for tc in text_chunks:
        entry: dict = {
            "chunk_id": make_chunk_id(
                corpus_file.source_type,
                doc_hash,
                tc.chunk_index,
                source_path=corpus_file.source_path,
                disambiguate=disambiguate,
            ),
            "chunk_index": tc.chunk_index,
            "text": tc.text,
            "source_file": basename,
            "source_path": corpus_file.source_path,
            "source_type": corpus_file.source_type,
            "document_title": document_title,
            "page_start": tc.page_start,
            "page_end": tc.page_end,
            "section_heading": tc.section_heading or "",
            "char_offset": tc.char_offset,
            "content_hash": doc_hash,
            "token_estimate": tc.token_estimate,
            "content_format": "pdf",
            "doc_category": corpus_file.doc_category,
        }
        if context_doc_path:
            entry["context_doc_path"] = context_doc_path
        if context_doc_excerpt:
            entry["context_doc_excerpt"] = context_doc_excerpt
        chunks.append(entry)

    record = SourceFileRecord(
        source_path=corpus_file.source_path,
        content_hash=doc_hash,
        page_count=extracted.page_count,
        chunk_count=len(text_chunks),
        content_format="pdf",
        doc_category=corpus_file.doc_category,
        needs_ocr_pages=extracted.needs_ocr_pages,
    )
    return chunks, record


def _build_chunks_from_markdown(
    corpus_file: CorpusFile,
    *,
    disambiguate: bool = False,
) -> tuple[list[dict], SourceFileRecord | None]:
    extracted = extract_markdown(corpus_file.path, corpus_file.source_path)
    if not extracted.full_text.strip():
        return [], None

    md_chunks = chunk_markdown(extracted.full_text)
    doc_hash = content_hash(extracted.full_text)
    document_title = _document_title(corpus_file)
    basename = corpus_file.path.name

    chunks: list[dict] = []
    for mc in md_chunks:
        chunks.append(
            {
                "chunk_id": make_chunk_id(
                    corpus_file.source_type,
                    doc_hash,
                    mc["chunk_index"],
                    source_path=corpus_file.source_path,
                    disambiguate=disambiguate,
                ),
                "chunk_index": mc["chunk_index"],
                "text": mc["text"],
                "source_file": basename,
                "source_path": corpus_file.source_path,
                "source_type": corpus_file.source_type,
                "document_title": document_title,
                "page_start": mc["page_start"],
                "page_end": mc["page_end"],
                "section_heading": mc.get("section_heading", ""),
                "char_offset": mc["char_offset"],
                "content_hash": doc_hash,
                "token_estimate": mc["token_estimate"],
                "content_format": "markdown",
                "doc_category": corpus_file.doc_category,
            }
        )

    record = SourceFileRecord(
        source_path=corpus_file.source_path,
        content_hash=doc_hash,
        page_count=1,
        chunk_count=len(chunks),
        content_format="markdown",
        doc_category=corpus_file.doc_category,
    )
    return chunks, record


def _manifests_equivalent(
    new_chunks: list[dict],
    new_files: list[SourceFileRecord],
    latest: Manifest,
) -> bool:
    if len(new_chunks) != len(latest.chunks):
        return False
    if {sf.source_path for sf in new_files} != {sf.source_path for sf in latest.source_files}:
        return False
    latest_map = {c["chunk_id"]: c for c in latest.chunks}
    compare_keys = (
        "source_path",
        "doc_category",
        "content_format",
        "context_doc_path",
        "context_doc_excerpt",
        "text",
    )
    for chunk in new_chunks:
        prev = latest_map.get(chunk["chunk_id"])
        if not prev:
            return False
        for key in compare_keys:
            if prev.get(key) != chunk.get(key):
                return False
    return True


def _sidecar_context(corpus_file: CorpusFile) -> tuple[str | None, str | None]:
    if corpus_file.content_format != "pdf":
        return None, None
    sidecar = sidecar_context_for_dir(corpus_file.path.parent)
    if not sidecar:
        return None, None
    md_name, excerpt = sidecar
    rel_dir = corpus_file.path.parent.relative_to(get_settings().root)
    context_path = str(rel_dir / md_name).replace("\\", "/")
    return context_path, excerpt


def parse_corpus(
    source: str = "all",
    force: bool = False,
    dry_run: bool = False,
) -> ParseResult:
    corpus_files = collect_corpus_files(source)
    if not corpus_files:
        return ParseResult(None, True, "No corpus files found for selected source.")

    latest = load_latest_manifest()
    prev_by_path = latest.chunks_by_source_path() if latest else {}
    prev_files = latest.source_files_by_path() if latest else {}
    current_paths = {f.source_path for f in corpus_files}
    hash_owner: dict[str, str] = {}

    all_chunks: list[dict] = []
    source_files: list[SourceFileRecord] = []
    source_hashes: list[str] = []
    dry_run_counts: dict[str, int] = {}

    counts = {"new_changed": 0, "reused": 0, "moved": 0, "empty": 0}

    for corpus_file in corpus_files:
        rel = corpus_file.source_path

        if corpus_file.content_format == "markdown":
            extracted = extract_markdown(corpus_file.path, rel)
            file_hash = content_hash(extracted.full_text)
            if not extracted.full_text.strip():
                counts["empty"] += 1
                continue
        else:
            extracted = extract_pdf(corpus_file.path, rel)
            file_hash = content_hash(extracted.full_text)

        prev = prev_files.get(rel) if latest and not force else None
        context_path, context_excerpt = _sidecar_context(corpus_file)

        if not force and prev and prev.content_hash == file_hash and rel in prev_by_path:
            reused = _rewrite_chunk_paths(
                prev_by_path[rel],
                source_path=rel,
                source_file=corpus_file.path.name,
                doc_category=corpus_file.doc_category,
                content_format=corpus_file.content_format,
                context_doc_path=context_path,
                context_doc_excerpt=context_excerpt,
            )
            dry_run_counts[rel] = len(reused)
            if dry_run:
                counts["reused"] += 1
                continue
            all_chunks.extend(reused)
            source_files.append(prev)
            source_hashes.append(file_hash)
            hash_owner.setdefault(file_hash, rel)
            counts["reused"] += 1
            continue

        if not force and prev is None and latest:
            old_path = find_by_content_hash(latest, file_hash)
            if old_path and old_path in prev_by_path and old_path not in current_paths:
                moved = _rewrite_chunk_paths(
                    prev_by_path[old_path],
                    source_path=rel,
                    source_file=corpus_file.path.name,
                    doc_category=corpus_file.doc_category,
                    content_format=corpus_file.content_format,
                    context_doc_path=context_path,
                    context_doc_excerpt=context_excerpt,
                )
                dry_run_counts[rel] = len(moved)
                if dry_run:
                    counts["moved"] += 1
                    continue
                all_chunks.extend(moved)
                old_record = prev_files[old_path]
                source_files.append(
                    SourceFileRecord(
                        source_path=rel,
                        content_hash=file_hash,
                        page_count=old_record.page_count,
                        chunk_count=len(moved),
                        content_format=corpus_file.content_format,
                        doc_category=corpus_file.doc_category,
                        needs_ocr_pages=old_record.needs_ocr_pages,
                    )
                )
                source_hashes.append(file_hash)
                hash_owner.setdefault(file_hash, rel)
                counts["moved"] += 1
                continue

        disambiguate = file_hash in hash_owner and hash_owner[file_hash] != rel

        if corpus_file.content_format == "markdown":
            chunks, record = _build_chunks_from_markdown(corpus_file, disambiguate=disambiguate)
            if record is None:
                counts["empty"] += 1
                continue
        else:
            chunks, record = _build_chunks_from_pdf(
                corpus_file,
                context_doc_path=context_path,
                context_doc_excerpt=context_excerpt,
                disambiguate=disambiguate,
            )

        dry_run_counts[rel] = len(chunks)
        if dry_run:
            counts["new_changed"] += 1
            continue

        all_chunks.extend(chunks)
        source_files.append(record)
        source_hashes.append(file_hash)
        hash_owner.setdefault(file_hash, rel)
        counts["new_changed"] += 1

    if dry_run:
        total = sum(dry_run_counts.values())
        return ParseResult(
            None,
            False,
            (
                f"Dry run: {counts['new_changed']} new/changed, "
                f"{counts['reused']} reused, {counts['moved']} moved, "
                f"{counts['empty']} empty → {total} chunks."
            ),
            dry_run_counts=dry_run_counts,
        )

    if not all_chunks:
        return ParseResult(None, True, "No chunks produced (all files empty?).")

    if not force and latest and _manifests_equivalent(all_chunks, source_files, latest):
        return ParseResult(
            latest,
            True,
            (
                f"Corpus unchanged; using manifest {latest.manifest_id} "
                f"({latest.stats.get('total_chunks', 0)} chunks)."
            ),
        )

    by_type: dict[str, int] = {}
    for ch in all_chunks:
        by_type[ch["source_type"]] = by_type.get(ch["source_type"], 0) + 1

    prev_chunk_count = latest.stats.get("total_chunks", 0) if latest else 0
    new_chunk_delta = len(all_chunks) - prev_chunk_count

    manifest = Manifest(
        manifest_id=make_manifest_id(source_hashes),
        created_at=datetime.now(timezone.utc).isoformat(),
        ingest_version=INGEST_VERSION,
        source_files=source_files,
        chunks=all_chunks,
        stats={
            "total_chunks": len(all_chunks),
            "total_tokens_estimate": sum(c["token_estimate"] for c in all_chunks),
            "by_source_type": by_type,
            "files_parsed": counts["new_changed"],
            "files_reused": counts["reused"],
            "files_moved": counts["moved"],
            "files_empty": counts["empty"],
            "chunk_delta": new_chunk_delta,
        },
        previous_manifest_id=latest.manifest_id if latest else None,
    )
    write_manifest(manifest, previous_manifest_id=latest.manifest_id if latest else None)

    delta_str = f"+{new_chunk_delta}" if new_chunk_delta >= 0 else str(new_chunk_delta)
    return ParseResult(
        manifest,
        False,
        (
            f"Parsed {counts['new_changed']} new/changed, reused {counts['reused']}, "
            f"moved {counts['moved']}, skipped {counts['empty']} empty. "
            f"Manifest {manifest.manifest_id} → {len(all_chunks)} chunks ({delta_str})."
        ),
    )


def count_pdfs() -> dict[str, int]:
    """Backward-compatible PDF counts for status display."""
    counts = count_corpus_files()
    return {
        "hoa": counts["hoa"],
        "bylaws": counts["hoa"],
        "county": counts["county"],
        "pdf": counts["pdf"],
        "markdown": counts["markdown"],
        "total": counts["total"],
    }

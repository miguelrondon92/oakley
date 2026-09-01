"""Markdown extraction and chunking."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pathlib import Path

from oakley.ingest.chunk import chunk_document, estimate_tokens

HEADING_PATTERN = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


@dataclass
class ExtractedMarkdown:
    source_path: str
    full_text: str
    page_count: int = 1


def extract_markdown(md_path: str | Path, source_path: str) -> ExtractedMarkdown:
    path = Path(md_path)
    text = path.read_text(encoding="utf-8").strip()
    return ExtractedMarkdown(source_path=source_path, full_text=text)


def chunk_markdown(full_text: str) -> list[dict]:
    """Chunk markdown by headings; fall back to size-based chunking."""
    if not full_text.strip():
        return []

    sections: list[tuple[str, str]] = []
    matches = list(HEADING_PATTERN.finditer(full_text))

    if not matches:
        segments = [(1, full_text)]
        raw_chunks = chunk_document(full_text, segments)
        return [_chunk_dict(c, "") for c in raw_chunks]

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        heading = match.group(2).strip()
        body = full_text[start:end].strip()
        if body:
            sections.append((heading, body))

    if not sections:
        segments = [(1, full_text)]
        raw_chunks = chunk_document(full_text, segments)
        return [_chunk_dict(c, "") for c in raw_chunks]

    chunks: list[dict] = []
    chunk_index = 0
    char_offset = 0

    for heading, body in sections:
        segments = [(1, body)]
        section_chunks = chunk_document(body, segments)
        for sc in section_chunks:
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "text": sc.text,
                    "page_start": 1,
                    "page_end": 1,
                    "section_heading": heading,
                    "char_offset": char_offset,
                    "token_estimate": estimate_tokens(sc.text),
                }
            )
            chunk_index += 1
            char_offset += len(sc.text)

    return chunks


def _chunk_dict(tc, heading: str) -> dict:
    return {
        "chunk_index": tc.chunk_index,
        "text": tc.text,
        "page_start": 1,
        "page_end": 1,
        "section_heading": heading or tc.section_heading or "",
        "char_offset": tc.char_offset,
        "token_estimate": tc.token_estimate,
    }


def sidecar_context_for_dir(directory: Path) -> tuple[str, str] | None:
    """Return (context_doc_path relative hint, excerpt) for first .md in directory."""
    md_files = sorted(directory.glob("*.md"))
    if not md_files:
        return None
    md = md_files[0]
    text = md.read_text(encoding="utf-8").strip()
    if not text:
        return None
    excerpt = text[:500].replace("\n", " ")
    return (md.name, excerpt)

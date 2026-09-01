"""Section-aware text chunking."""

from __future__ import annotations

import re
from dataclasses import dataclass

from oakley.config import MIN_CHUNK_CHARS, OVERLAP_TOKENS, TARGET_TOKENS

SECTION_PATTERN = re.compile(
    r"^(?:"
    r"(?:ARTICLE|Article|SECTION|Section)\s+[IVXLC\d]+[\.\:\-\s].*|"
    r"[A-Z][A-Z0-9\s\-]{4,}$"
    r")",
    re.MULTILINE,
)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass
class TextChunk:
    text: str
    chunk_index: int
    page_start: int
    page_end: int
    section_heading: str
    char_offset: int
    token_estimate: int


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _find_sections(full_text: str) -> list[tuple[int, str]]:
    sections: list[tuple[int, str]] = [(0, "")]
    for match in SECTION_PATTERN.finditer(full_text):
        heading = match.group(0).strip()
        if len(heading) > 3:
            sections.append((match.start(), heading))
    sections.sort(key=lambda x: x[0])
    return sections


def _page_for_offset(page_offsets: list[tuple[int, int]], char_pos: int) -> int:
    for page_num, start in page_offsets:
        if char_pos >= start:
            current = page_num
        else:
            break
    return current


def _split_at_sentences(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            window = text[start:end]
            last_break = max(window.rfind(". "), window.rfind(".\n"), window.rfind("! "), window.rfind("? "))
            if last_break > max_chars // 3:
                end = start + last_break + 1
        piece = text[start:end].strip()
        if piece:
            parts.append(piece)
        start = end
    return parts


def build_page_offsets(pages: list[tuple[int, str]]) -> list[tuple[int, int]]:
    """List of (page_num, char_offset) from sequential page texts."""
    offsets: list[tuple[int, int]] = []
    pos = 0
    for page_num, text in pages:
        offsets.append((page_num, pos))
        pos += len(text) + 2  # \n\n separator
    return offsets


def chunk_document(
    full_text: str,
    page_segments: list[tuple[int, str]],
    target_tokens: int = TARGET_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
    min_chunk_chars: int = MIN_CHUNK_CHARS,
) -> list[TextChunk]:
    if not full_text.strip():
        return []

    max_chars = target_tokens * 4
    overlap_chars = overlap_tokens * 4
    page_offsets = build_page_offsets(page_segments)
    sections = _find_sections(full_text)

    # Build section spans
    spans: list[tuple[int, int, str]] = []
    for idx, (start, heading) in enumerate(sections):
        end = sections[idx + 1][0] if idx + 1 < len(sections) else len(full_text)
        if end > start:
            spans.append((start, end, heading))

    if not spans:
        spans = [(0, len(full_text), "")]

    raw_pieces: list[tuple[str, int, str]] = []
    for start, end, heading in spans:
        section_text = full_text[start:end].strip()
        if not section_text:
            continue
        for piece in _split_at_sentences(section_text, max_chars):
            raw_pieces.append((piece, start + section_text.find(piece), heading))

    if not raw_pieces:
        for piece in _split_at_sentences(full_text, max_chars):
            raw_pieces.append((piece, full_text.find(piece), ""))

    chunks: list[TextChunk] = []
    prev_tail = ""
    chunk_index = 0

    for text, char_offset, heading in raw_pieces:
        combined = f"{prev_tail}{text}".strip() if prev_tail else text
        if len(combined) < min_chunk_chars and chunks:
            chunks[-1] = TextChunk(
                text=chunks[-1].text + "\n\n" + combined,
                chunk_index=chunks[-1].chunk_index,
                page_start=chunks[-1].page_start,
                page_end=_page_for_offset(page_offsets, char_offset + len(combined)),
                section_heading=heading or chunks[-1].section_heading,
                char_offset=chunks[-1].char_offset,
                token_estimate=estimate_tokens(chunks[-1].text + combined),
            )
            continue

        page_start = _page_for_offset(page_offsets, char_offset)
        page_end = _page_for_offset(page_offsets, char_offset + len(combined))
        prefix = f"[{heading}]\n\n" if heading and not combined.startswith("[") else ""
        body = prefix + combined

        chunks.append(
            TextChunk(
                text=body,
                chunk_index=chunk_index,
                page_start=page_start,
                page_end=page_end,
                section_heading=heading,
                char_offset=char_offset,
                token_estimate=estimate_tokens(body),
            )
        )
        chunk_index += 1

        if overlap_chars > 0 and len(text) > overlap_chars:
            prev_tail = text[-overlap_chars:]
        else:
            prev_tail = ""

    for i, ch in enumerate(chunks):
        chunks[i] = TextChunk(
            text=ch.text,
            chunk_index=i,
            page_start=ch.page_start,
            page_end=ch.page_end,
            section_heading=ch.section_heading,
            char_offset=ch.char_offset,
            token_estimate=ch.token_estimate,
        )

    return chunks

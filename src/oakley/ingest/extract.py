"""PDF text extraction via PyMuPDF."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from oakley.config import LOW_DENSITY_PAGE_CHARS


@dataclass
class PageText:
    page_num: int  # 1-based
    text: str
    char_count: int
    needs_ocr: bool


@dataclass
class ExtractedDocument:
    source_path: str
    pages: list[PageText]
    full_text: str
    needs_ocr_pages: list[int]

    @property
    def page_count(self) -> int:
        return len(self.pages)


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    cleaned: list[str] = []
    for line in lines:
        if not line:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def extract_pdf(pdf_path: Path, source_path: str) -> ExtractedDocument:
    pages: list[PageText] = []
    needs_ocr_pages: list[int] = []
    parts: list[str] = []

    with pymupdf.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            page_num = i + 1
            raw = page.get_text("text") or ""
            text = _clean_text(raw)
            char_count = len(text)
            needs_ocr = char_count < LOW_DENSITY_PAGE_CHARS
            if needs_ocr:
                needs_ocr_pages.append(page_num)
            pages.append(
                PageText(
                    page_num=page_num,
                    text=text,
                    char_count=char_count,
                    needs_ocr=needs_ocr,
                )
            )
            if text:
                parts.append(text)

    full_text = "\n\n".join(parts)
    return ExtractedDocument(
        source_path=source_path,
        pages=pages,
        full_text=full_text,
        needs_ocr_pages=needs_ocr_pages,
    )

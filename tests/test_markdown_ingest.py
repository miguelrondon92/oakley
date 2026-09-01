"""Tests for markdown ingestion and companion metadata."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from oakley.ingest.markdown import chunk_markdown, extract_markdown, sidecar_context_for_dir
from oakley.ingest.parse import parse_corpus


def _write_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


@pytest.fixture
def md_corpus(tmp_path, monkeypatch):
    root = tmp_path / "oakley"
    dr = root / "hoa_docs" / "policies" / "deed_restrictions"
    faqs = root / "hoa_docs" / "faqs"
    dr.mkdir(parents=True)
    faqs.mkdir(parents=True)

    (dr / "deed_restrictions.md").write_text(
        "# Deed Restrictions\n\nOverview of restrictions for the community.\n\n"
        "## Section A\n\nNo commercial vehicles in driveways.",
        encoding="utf-8",
    )
    _write_pdf(dr / "section-1.pdf", "Deed restriction section one text.")
    (faqs / "faqs.md").write_text(
        "# FAQs\n\n## Q: Can I park an RV?\n\nA: RVs must be screened from view.",
        encoding="utf-8",
    )

    import oakley.config as config_module

    config_module._settings = None
    monkeypatch.setattr(config_module, "repo_root", lambda: root)
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    config_module._settings = None
    yield root
    config_module._settings = None


def test_chunk_markdown_by_headings():
    text = "# Title\n\nIntro.\n\n## Section One\n\nBody one.\n\n## Section Two\n\nBody two."
    chunks = chunk_markdown(text)
    assert len(chunks) >= 2
    assert all(c["page_start"] == 1 for c in chunks)
    assert any("Section One" in c.get("section_heading", "") for c in chunks)


def test_extract_markdown():
    path = Path("dummy.md")
    # use tmp inline
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Hello\n\nWorld.")
        f.flush()
        extracted = extract_markdown(f.name, "hoa_docs/faqs/faqs.md")
    assert "Hello" in extracted.full_text
    assert extracted.page_count == 1


def test_sidecar_context():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        (directory / "notes.md").write_text("Context about this folder.", encoding="utf-8")
        result = sidecar_context_for_dir(directory)
        assert result is not None
        name, excerpt = result
        assert name == "notes.md"
        assert "Context" in excerpt


def test_pdf_companion_metadata(md_corpus):
    result = parse_corpus(source="hoa")
    assert result.manifest is not None
    pdf_chunks = [
        c
        for c in result.manifest.chunks
        if c["source_path"] == "hoa_docs/policies/deed_restrictions/section-1.pdf"
    ]
    assert pdf_chunks
    assert pdf_chunks[0].get("context_doc_path") == "hoa_docs/policies/deed_restrictions/deed_restrictions.md"
    assert pdf_chunks[0].get("context_doc_excerpt")


def test_markdown_indexed_as_chunks(md_corpus):
    result = parse_corpus(source="hoa")
    md_chunks = [c for c in result.manifest.chunks if c.get("content_format") == "markdown"]
    assert len(md_chunks) >= 2
    assert any(c["doc_category"] == "faqs" for c in md_chunks)
    assert any(c["doc_category"] == "deed_restrictions" for c in md_chunks)

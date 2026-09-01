"""Tests for section-aware chunking."""

from oakley.ingest.chunk import chunk_document, estimate_tokens


def test_estimate_tokens():
    assert estimate_tokens("hello world") >= 1


def test_chunk_document_splits_long_text():
    pages = [(1, "Intro paragraph. " * 50)]
    full = pages[0][1]
    chunks = chunk_document(full, pages, target_tokens=50, overlap_tokens=10, min_chunk_chars=20)
    assert len(chunks) >= 1
    assert all(c.token_estimate > 0 for c in chunks)
    assert chunks[0].page_start == 1


def test_chunk_document_section_heading():
    text = "ARTICLE IV\n\nArchitectural control rules apply to all improvements.\n\n" * 5
    pages = [(1, text)]
    chunks = chunk_document(text, pages, target_tokens=100, overlap_tokens=10, min_chunk_chars=10)
    assert len(chunks) >= 1
    assert any("ARTICLE" in (c.section_heading or c.text) for c in chunks)


def test_empty_document():
    assert chunk_document("", []) == []

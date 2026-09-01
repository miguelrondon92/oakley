"""Tests for manifest schema validation."""

from oakley.ingest.manifest import Manifest, SourceFileRecord, validate_manifest


def _sample_chunk(**overrides):
    base = {
        "chunk_id": "hoa_bylaw:abc:0",
        "chunk_index": 0,
        "text": "Sample chunk text for testing.",
        "source_file": "test.pdf",
        "source_path": "bylaws/test.pdf",
        "source_type": "hoa_bylaw",
        "document_title": "Test Document",
        "page_start": 1,
        "page_end": 1,
        "section_heading": "",
        "char_offset": 0,
        "content_hash": "abc",
        "token_estimate": 10,
        "content_format": "pdf",
        "doc_category": "bylaws",
    }
    base.update(overrides)
    return base


def test_validate_manifest_ok():
    manifest = Manifest(
        manifest_id="20260101-abc123",
        created_at="2026-01-01T00:00:00Z",
        ingest_version="1",
        source_files=[
            SourceFileRecord(
                source_path="bylaws/test.pdf",
                content_hash="abc",
                page_count=1,
                chunk_count=1,
            )
        ],
        chunks=[_sample_chunk()],
        stats={"total_chunks": 1, "total_tokens_estimate": 10, "by_source_type": {"hoa_bylaw": 1}},
    )
    assert validate_manifest(manifest) == []


def test_validate_manifest_duplicate_id():
    manifest = Manifest(
        manifest_id="20260101-abc123",
        created_at="2026-01-01T00:00:00Z",
        ingest_version="1",
        source_files=[],
        chunks=[_sample_chunk(), _sample_chunk()],
        stats={},
    )
    errors = validate_manifest(manifest)
    assert any("Duplicate" in e for e in errors)


def test_validate_manifest_bad_pages():
    manifest = Manifest(
        manifest_id="20260101-abc123",
        created_at="2026-01-01T00:00:00Z",
        ingest_version="1",
        source_files=[],
        chunks=[_sample_chunk(page_start=5, page_end=2)],
        stats={},
    )
    errors = validate_manifest(manifest)
    assert any("page_start" in e for e in errors)

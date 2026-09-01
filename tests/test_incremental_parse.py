"""Tests for incremental parse behavior."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from oakley.ingest.parse import parse_corpus


def _write_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def _build_corpus(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "oakley"
    (root / "hoa_docs" / "bylaws").mkdir(parents=True)
    (root / "hoa_docs" / "policies").mkdir(parents=True)
    (root / "county_regulations").mkdir(parents=True)

    _write_pdf(root / "hoa_docs" / "bylaws" / "alpha.pdf", "Alpha bylaw content.")
    _write_pdf(root / "hoa_docs" / "bylaws" / "beta.pdf", "Beta bylaw content.")
    _write_pdf(root / "county_regulations" / "county.pdf", "County regulation text.")

    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    import oakley.config as config_module

    config_module._settings = None
    monkeypatch.setattr(
        config_module,
        "repo_root",
        lambda: root,
    )
    return root


@pytest.fixture
def corpus_env(tmp_path, monkeypatch):
    root = _build_corpus(tmp_path, monkeypatch)
    import oakley.config as config_module

    config_module._settings = None
    yield root
    config_module._settings = None


def test_parse_new_corpus(corpus_env):
    result = parse_corpus(source="all")
    assert result.manifest is not None
    assert not result.skipped
    assert result.manifest.stats["total_chunks"] >= 3


def test_parse_reuses_unchanged_hash(corpus_env, tmp_path):
    first = parse_corpus(source="all")
    assert first.manifest is not None
    manifest_id = first.manifest.manifest_id

    second = parse_corpus(source="all")
    assert second.skipped
    assert second.manifest.manifest_id == manifest_id
    assert "unchanged" in second.message.lower()


def test_parse_processes_new_file_only(corpus_env):
    parse_corpus(source="all")
    _write_pdf(
        corpus_env / "hoa_docs" / "policies" / "new-policy.pdf",
        "Brand new policy document content.",
    )

    result = parse_corpus(source="all")
    assert result.manifest is not None
    assert result.manifest.stats.get("files_parsed", 0) >= 1
    paths = {sf.source_path for sf in result.manifest.source_files}
    assert "hoa_docs/policies/new-policy.pdf" in paths


def test_parse_path_move_reuse(corpus_env):
    alpha = corpus_env / "hoa_docs" / "bylaws" / "alpha.pdf"
    text = alpha.read_bytes()
    first = parse_corpus(source="hoa")
    assert first.manifest is not None
    old_path = "hoa_docs/bylaws/alpha.pdf"
    old_hash = first.manifest.source_files_by_path()[old_path].content_hash
    old_chunks = first.manifest.chunks_by_source_path()[old_path]

    alpha.unlink()
    moved = corpus_env / "hoa_docs" / "policies" / "alpha.pdf"
    moved.write_bytes(text)

    result = parse_corpus(source="all")
    assert result.manifest is not None
    new_path = "hoa_docs/policies/alpha.pdf"
    assert new_path in result.manifest.source_files_by_path()
    assert result.manifest.source_files_by_path()[new_path].content_hash == old_hash
    moved_chunks = result.manifest.chunks_by_source_path()[new_path]
    assert moved_chunks[0]["text"] == old_chunks[0]["text"]
    assert moved_chunks[0]["chunk_id"] == old_chunks[0]["chunk_id"]


def test_parse_dry_run_counts(corpus_env):
    result = parse_corpus(source="all", dry_run=True)
    assert result.dry_run_counts
    assert len(result.dry_run_counts) >= 3

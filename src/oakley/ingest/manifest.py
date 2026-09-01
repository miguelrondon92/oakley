"""Chunk manifest read/write and validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oakley.config import INGEST_VERSION, get_settings, resolve_path

REQUIRED_CHUNK_FIELDS = {
    "chunk_id",
    "chunk_index",
    "text",
    "source_file",
    "source_path",
    "source_type",
    "document_title",
    "page_start",
    "page_end",
    "section_heading",
    "char_offset",
    "content_hash",
    "token_estimate",
    "content_format",
    "doc_category",
}


@dataclass
class SourceFileRecord:
    source_path: str
    content_hash: str
    page_count: int
    chunk_count: int
    content_format: str = "pdf"
    doc_category: str = ""
    needs_ocr_pages: list[int] = field(default_factory=list)


@dataclass
class Manifest:
    manifest_id: str
    created_at: str
    ingest_version: str
    source_files: list[SourceFileRecord]
    chunks: list[dict[str, Any]]
    stats: dict[str, Any]
    previous_manifest_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "manifest_id": self.manifest_id,
            "created_at": self.created_at,
            "ingest_version": self.ingest_version,
            "source_files": [asdict(sf) for sf in self.source_files],
            "chunks": self.chunks,
            "stats": self.stats,
        }
        if self.previous_manifest_id:
            data["previous_manifest_id"] = self.previous_manifest_id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manifest:
        source_files = []
        for sf in data["source_files"]:
            kwargs = dict(sf)
            kwargs.setdefault("content_format", "pdf")
            kwargs.setdefault("doc_category", "")
            source_files.append(SourceFileRecord(**kwargs))
        return cls(
            manifest_id=data["manifest_id"],
            created_at=data["created_at"],
            ingest_version=data["ingest_version"],
            source_files=source_files,
            chunks=data["chunks"],
            stats=data["stats"],
            previous_manifest_id=data.get("previous_manifest_id"),
        )

    def source_files_by_path(self) -> dict[str, SourceFileRecord]:
        return {sf.source_path: sf for sf in self.source_files}

    def chunks_by_source_path(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for chunk in self.chunks:
            grouped.setdefault(chunk["source_path"], []).append(chunk)
        return grouped


def content_hash(text: str) -> str:
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def make_chunk_id(
    source_type: str,
    doc_hash: str,
    chunk_index: int,
    *,
    source_path: str | None = None,
    disambiguate: bool = False,
) -> str:
    if disambiguate and source_path:
        path_part = hashlib.sha256(source_path.encode()).hexdigest()[:8]
        return f"{source_type}:{doc_hash}:{path_part}:{chunk_index}"
    return f"{source_type}:{doc_hash}:{chunk_index}"


def make_manifest_id(source_hashes: list[str]) -> str:
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    combined = "|".join(sorted(source_hashes))
    short = hashlib.sha256(combined.encode()).hexdigest()[:6]
    return f"{date_part}-{short}"


def find_by_content_hash(manifest: Manifest, doc_hash: str) -> str | None:
    for sf in manifest.source_files:
        if sf.content_hash == doc_hash:
            return sf.source_path
    return None


def validate_manifest(manifest: Manifest) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for chunk in manifest.chunks:
        missing = REQUIRED_CHUNK_FIELDS - set(chunk.keys())
        if missing:
            errors.append(f"Chunk {chunk.get('chunk_index')}: missing {missing}")
        cid = chunk.get("chunk_id")
        if cid in seen_ids:
            errors.append(f"Duplicate chunk_id: {cid}")
        seen_ids.add(cid)
        if chunk.get("page_start", 0) > chunk.get("page_end", 0):
            errors.append(f"Chunk {cid}: page_start > page_end")
        fmt = chunk.get("content_format")
        if fmt not in ("pdf", "markdown"):
            errors.append(f"Chunk {cid}: invalid content_format {fmt!r}")
    return errors


def processed_root() -> Path:
    settings = get_settings()
    return resolve_path(settings.processed_dir, settings)


def latest_pointer_path() -> Path:
    return processed_root() / "latest.json"


def manifest_dir(manifest_id: str) -> Path:
    return processed_root() / manifest_id


def manifest_path(manifest_id: str) -> Path:
    return manifest_dir(manifest_id) / "chunk_manifest.json"


def write_manifest(manifest: Manifest, previous_manifest_id: str | None = None) -> Path:
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("Invalid manifest: " + "; ".join(errors))

    out_dir = manifest_dir(manifest.manifest_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "chunk_manifest.json"
    out_file.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

    pointer = {
        "manifest_id": manifest.manifest_id,
        "path": str(out_file.relative_to(get_settings().root)),
        "created_at": manifest.created_at,
    }
    if previous_manifest_id:
        pointer["previous_manifest_id"] = previous_manifest_id
    latest_pointer_path().parent.mkdir(parents=True, exist_ok=True)
    latest_pointer_path().write_text(json.dumps(pointer, indent=2), encoding="utf-8")
    return out_file


def load_latest_manifest() -> Manifest | None:
    pointer = latest_pointer_path()
    if not pointer.exists():
        return None
    data = json.loads(pointer.read_text(encoding="utf-8"))
    manifest_file = get_settings().root / data["path"]
    if not manifest_file.exists():
        return None
    manifest = Manifest.from_dict(json.loads(manifest_file.read_text(encoding="utf-8")))
    if not manifest.previous_manifest_id and data.get("previous_manifest_id"):
        manifest.previous_manifest_id = data["previous_manifest_id"]
    return manifest


def load_previous_manifest(manifest: Manifest) -> Manifest | None:
    prev_id = manifest.previous_manifest_id
    if not prev_id:
        pointer = latest_pointer_path()
        if pointer.exists():
            data = json.loads(pointer.read_text(encoding="utf-8"))
            prev_id = data.get("previous_manifest_id")
    if not prev_id:
        return None
    try:
        return load_manifest(prev_id)
    except FileNotFoundError:
        return None


def load_manifest(manifest_id: str) -> Manifest:
    path = manifest_path(manifest_id)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_id}")
    return Manifest.from_dict(json.loads(path.read_text(encoding="utf-8")))


def clean_processed() -> int:
    root = processed_root()
    if not root.exists():
        return 0
    count = sum(1 for _ in root.rglob("*") if _.is_file())
    import shutil

    shutil.rmtree(root)
    return count

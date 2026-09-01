"""Corpus file discovery from CORPUS_ROOTS registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from oakley.config import CORPUS_ROOTS, get_settings


@dataclass(frozen=True)
class CorpusFile:
    path: Path
    source_path: str
    source_type: str
    doc_category: str
    content_format: str  # pdf | markdown


def _normalize_source(source: str) -> str:
    if source == "bylaws":
        return "hoa"
    return source


def collect_corpus_files(source: str = "all") -> list[CorpusFile]:
    settings = get_settings()
    root = settings.root
    source = _normalize_source(source)

    if source not in ("all", "hoa", "county"):
        raise ValueError(f"Unknown source: {source}. Use hoa, county, or all.")

    files: list[CorpusFile] = []
    seen_paths: set[str] = set()

    for rel_root, source_type, doc_category, formats in CORPUS_ROOTS:
        if source == "hoa" and source_type != "hoa_bylaw":
            continue
        if source == "county" and source_type != "county_regulation":
            continue

        base = root / rel_root
        if not base.exists():
            continue

        patterns: list[tuple[str, str, bool]] = []
        if "pdf" in formats:
            recursive = rel_root not in ("hoa_docs/policies",)
            patterns.append(("**/*.pdf" if recursive else "*.pdf", "pdf", recursive))
        if "md" in formats:
            patterns.append(("**/*.md", "markdown", True))

        for pattern, fmt, _recursive in patterns:
            for path in sorted(base.glob(pattern)):
                if not path.is_file():
                    continue
                rel = str(path.relative_to(root)).replace("\\", "/")
                if rel in seen_paths:
                    continue
                seen_paths.add(rel)
                files.append(
                    CorpusFile(
                        path=path,
                        source_path=rel,
                        source_type=source_type,
                        doc_category=doc_category,
                        content_format=fmt,
                    )
                )

    return files


def count_corpus_files() -> dict[str, int]:
    all_files = collect_corpus_files("all")
    hoa = sum(1 for f in all_files if f.source_type == "hoa_bylaw")
    county = sum(1 for f in all_files if f.source_type == "county_regulation")
    md = sum(1 for f in all_files if f.content_format == "markdown")
    pdf = sum(1 for f in all_files if f.content_format == "pdf")
    return {"hoa": hoa, "county": county, "pdf": pdf, "markdown": md, "total": len(all_files)}

"""Runtime configuration loaded from environment (never log secret values)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

COLLECTION_NAME = "oakley_corpus"
EMBEDDING_MODEL_DEFAULT = "models/gemini-embedding-001"
INGEST_VERSION = "2"
TARGET_TOKENS = 800
OVERLAP_TOKENS = 100
MIN_CHUNK_CHARS = 100
MIN_SCORE_THRESHOLD = 0.45
LOW_DENSITY_PAGE_CHARS = 50

# Document titles keyed by basename (from corpus-inventory.md)
DOCUMENT_TITLES: dict[str, str] = {
    "Recorded-OAKWOOD-GLEN-SECOND-AMENDED-AND-RESTATED-BYLAWS-03782964xC3D0.pdf": (
        "Oakwood Glen Bylaws (Second Amended and Restated)"
    ),
    "ACC-Denial-Letter-and-Appeal-Hearing-Policy_REAL-PROPERTY_2021.pdf": (
        "ACC Denial Letter and Appeal Hearing Policy"
    ),
    "Deed-Restriction-Violation-Hearing-Policy_REAL-PROPERTY_2021.pdf": (
        "Deed Restriction Violation Hearing Policy"
    ),
    "Large-Contract-Bid-Solicitation-Policy_REAL-PROPERTY_2021.pdf": (
        "Large Contract Bid Solicitation Policy"
    ),
    "OGA-Architectural-Review-Authority-Appointment-Policy-02573519xC3D0C.pdf": (
        "OGA Architectural Review Authority Appointment Policy"
    ),
    "Religious-Display-Policy_REAL-PROPERTY_2021.pdf": "Religious Display Policy",
    "Security-Measures-Policy_REAL-PROPERTY_2021.pdf": "Security Measures Policy",
    "Swimming-Pool-Enclosure-Policy_REAL-PROPERTY_2021.pdf": (
        "Swimming Pool Enclosure Policy"
    ),
    "Harris County Community Protections.pdf": "Harris County Community Protections",
    "Harris County Streets and Roads.pdf": "Harris County Streets and Roads",
    "Amendment-to-Collection-Policy.pdf": "Amendment to Collection Policy",
    "Candidate-Form-2024.pdf": "Candidate Form 2024",
    "Collection-Policy.pdf": "Collection Policy",
    "Conflict-of-Interest-Policy-RP-2016-302394.pdf": "Conflict of Interest Policy",
    "Notice-of-Association-Policies-20110545794.pdf": "Notice of Association Policies",
    "Oakwood-Glen-Amended-Deed-recorded-01147298xC3D0C.pdf": "Oakwood Glen Amended Deed",
    "Oakwood-Glen-Amended-Deed-recorded-01147298xC3D0C (1).pdf": "Oakwood Glen Amended Deed",
    "Policy-Regarding-Operation-of-a-Business-out-of-a-Home-Recorded.pdf": (
        "Policy Regarding Operation of a Business out of a Home"
    ),
    "RP-2017-283716-Email-Policy-Recorded-01128679xC3D0C.pdf": "Email Policy",
    "RP-2017-283767-Board-Resolution-Recorded-01128676xC3D0C.pdf": "Board Resolution",
    "RP-2017-283779-Electric-Generators-Regulation-Recorded-01128692xC3D0C.pdf": (
        "Electric Generators Regulation"
    ),
    "Recorded-Oakwood-Glen-Forced-Mow-Policy-01360517xC3D0C.pdf": "Forced Mow Policy",
    "Recorded-Oakwood-Glen-Operating-Reserve-Policy-01510621xC3D0C-1.pdf": (
        "Operating Reserve Policy"
    ),
    "Records-Production-Policy-20110545796.pdf": "Records Production Policy",
    "Records-Retention-Policy-20110545798.pdf": "Records Retention Policy",
    "Section-202.006-Affidavit-20110545795.pdf": "Section 202.006 Affidavit",
    "Deed-Restrictions-Section-1.pdf": "Deed Restrictions Section 1",
    "Deed-Restrictions-Section-2.pdf": "Deed Restrictions Section 2",
    "deed_restrictions.md": "Deed Restrictions Overview",
    "faqs.md": "Frequently Asked Questions",
}

# (rel_root, source_type, doc_category, formats)
CORPUS_ROOTS: list[tuple[str, str, str, list[str]]] = [
    ("hoa_docs/bylaws", "hoa_bylaw", "bylaws", ["pdf"]),
    ("hoa_docs/policies", "hoa_bylaw", "policies", ["pdf"]),
    ("hoa_docs/policies/deed_restrictions", "hoa_bylaw", "deed_restrictions", ["pdf", "md"]),
    ("hoa_docs/faqs", "hoa_bylaw", "faqs", ["md"]),
    ("county_regulations", "county_regulation", "county", ["pdf"]),
]

# Legacy alias — prefer CORPUS_ROOTS
SOURCE_DIRS = {
    "hoa": ("hoa_docs", "hoa_bylaw"),
    "bylaws": ("hoa_docs", "hoa_bylaw"),
    "county": ("county_regulations", "county_regulation"),
}


def repo_root() -> Path:
    """Project root (directory containing pyproject.toml)."""
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    gemini_model: str
    embedding_model: str
    chroma_persist_dir: Path
    processed_dir: Path
    db_path: Path
    host: str
    port: int
    top_k: int
    root: Path

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.strip())

    def require_gemini(self) -> str:
        if not self.gemini_configured:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key locally."
            )
        return self.gemini_api_key  # type: ignore[return-value]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        root = repo_root()
        load_dotenv(root / ".env", override=False)
        _settings = Settings(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            embedding_model=os.getenv("OAKLEY_EMBEDDING_MODEL", EMBEDDING_MODEL_DEFAULT),
            chroma_persist_dir=Path(os.getenv("CHROMA_PERSIST_DIR", "data/chroma/")),
            processed_dir=Path("data/processed"),
            db_path=Path(os.getenv("OAKLEY_DB_PATH", "data/oakley.db")),
            host=os.getenv("OAKLEY_HOST", "127.0.0.1"),
            port=int(os.getenv("OAKLEY_PORT", "8080")),
            top_k=int(os.getenv("OAKLEY_TOP_K", "5")),
            root=root,
        )
    return _settings


def resolve_path(path: Path, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    if path.is_absolute():
        return path
    return settings.root / path

"""Golden question integration tests (require GEMINI_API_KEY)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

from oakley.rag.answer import ask_question

FIXTURES = Path(__file__).parent / "fixtures" / "golden_questions.yaml"


@pytest.fixture(scope="module")
def golden_questions():
    with FIXTURES.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
def test_golden_questions(golden_questions):
    for case in golden_questions:
        result = ask_question(
            case["question"],
            source_type=case.get("source_type_filter"),
        )
        assert result["refused"] == case["expect_refused"], (
            f"Question: {case['question']!r} — expected refused={case['expect_refused']}, "
            f"got {result['refused']}. Answer: {result['answer'][:200]}"
        )
        if case.get("refusal_reason"):
            assert result.get("refusal_reason") == case["refusal_reason"]

        if not case["expect_refused"]:
            assert result["citations"], f"No citations for: {case['question']}"
            expected_file = case["expect_citation"]["source_file"]
            cited_files = {c["source_file"] for c in result["citations"]}
            assert expected_file in cited_files or any(
                expected_file in cid for cid in result["retrieved_chunk_ids"]
            ), f"Expected citation from {expected_file}, got {cited_files}"

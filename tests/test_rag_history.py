"""Tests for history-aware prompt building."""

from oakley.rag.answer import build_prompt, trim_history


def test_trim_history_limits_messages():
    history = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    trimmed = trim_history(history)
    assert len(trimmed) <= 10


def test_build_prompt_includes_history():
    chunks = [
        {
            "document_title": "Test Doc",
            "page_start": 1,
            "section_heading": "",
            "text": "Sample regulation text.",
            "chunk_id": "x:1:0",
        }
    ]
    history = [
        {"role": "user", "content": "Can I build a treehouse?"},
        {"role": "assistant", "content": "I need to check the bylaws."},
    ]
    prompt = build_prompt("What about ACC approval?", chunks, history=history)
    assert "Prior conversation:" in prompt
    assert "treehouse" in prompt
    assert "ACC approval" in prompt
    assert "Sample regulation text" in prompt


def test_build_prompt_without_history():
    chunks = [{"document_title": "Doc", "page_start": 1, "section_heading": "", "text": "Text", "chunk_id": "a"}]
    prompt = build_prompt("Question?", chunks, history=None)
    assert "Prior conversation:" not in prompt

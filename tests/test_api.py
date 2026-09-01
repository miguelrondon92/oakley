"""API tests with mocked RAG."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("OAKLEY_DB_PATH", str(tmp_path / "api_test.db"))
    from oakley import config

    config._settings = None
    yield
    config._settings = None


@pytest.fixture
def client():
    from oakley.api.app import app

    return TestClient(app)


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "status" in res.json()


def test_conversation_crud(client):
    create = client.post("/api/conversations", json={"title": "Test chat"})
    assert create.status_code == 201
    conv_id = create.json()["id"]

    get_one = client.get(f"/api/conversations/{conv_id}")
    assert get_one.status_code == 200
    assert get_one.json()["messages"] == []

    patch = client.patch(f"/api/conversations/{conv_id}", json={"source_type": "hoa_bylaw"})
    assert patch.status_code == 200
    assert patch.json()["source_type"] == "hoa_bylaw"

    delete = client.delete(f"/api/conversations/{conv_id}")
    assert delete.status_code == 204


@patch("oakley.api.app.ask_question")
def test_post_message(mock_ask, client):
    mock_ask.return_value = {
        "question": "Hello",
        "answer": "Test answer with citation.",
        "citations": [
            {
                "document_title": "Test Doc",
                "source_file": "test.pdf",
                "source_type": "hoa_bylaw",
                "page_start": 1,
                "page_end": 1,
                "section_heading": "",
                "chunk_id": "a:b:0",
                "quote": "Sample quote",
            }
        ],
        "retrieved_chunk_ids": ["a:b:0"],
        "confidence": "high",
        "refused": False,
        "refusal_reason": None,
        "provider_model": "gemini-test",
        "retrieval": {"top_k": 5, "filters": {}, "max_score": 0.9},
    }

    conv = client.post("/api/conversations", json={}).json()
    res = client.post(f"/api/conversations/{conv['id']}/messages", json={"content": "Hello"})
    assert res.status_code == 201
    data = res.json()
    assert data["assistant_message"]["content"] == "Test answer with citation."
    assert len(data["assistant_message"]["citations"]) == 1
    mock_ask.assert_called_once()
    call_kwargs = mock_ask.call_args.kwargs
    assert call_kwargs.get("history") == []

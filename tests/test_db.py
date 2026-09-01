"""Tests for conversation DB store."""

import pytest

from oakley.db import store as db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("OAKLEY_DB_PATH", str(db_path))
    from oakley import config

    config._settings = None
    db.init_db()
    yield
    config._settings = None


def test_create_and_list_conversations():
    c1 = db.create_conversation(title="First")
    c2 = db.create_conversation(title="Second")
    convs = db.list_conversations()
    ids = [c.id for c in convs]
    assert c1.id in ids
    assert c2.id in ids
    assert convs[0].title == "Second"


def test_messages_and_history():
    conv = db.create_conversation()
    db.add_message(conv.id, "user", "Hello")
    db.add_message(conv.id, "assistant", "Hi there")
    msgs = db.list_messages(conv.id)
    assert len(msgs) == 2
    history = db.message_history_for_rag(conv.id)
    assert len(history) == 2
    assert history[0]["role"] == "user"


def test_update_source_type():
    conv = db.create_conversation()
    updated = db.update_conversation(conv.id, source_type="hoa_bylaw")
    assert updated.source_type == "hoa_bylaw"


def test_delete_conversation():
    conv = db.create_conversation()
    assert db.delete_conversation(conv.id)
    assert db.get_conversation(conv.id) is None


def test_auto_title():
    title = db.auto_title_from_message("Can I build a treehouse in my backyard?")
    assert "treehouse" in title

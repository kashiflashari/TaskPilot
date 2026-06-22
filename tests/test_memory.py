from taskpilot.memory import InMemoryStore


def test_session_roundtrip():
    store = InMemoryStore()
    assert store.load_session("s1") is None
    store.save_session("s1", {"goal": "g", "history": [1, 2]})
    assert store.load_session("s1") == {"goal": "g", "history": [1, 2]}


def test_pending_lifecycle():
    store = InMemoryStore()
    store.save_pending("a1", {"tool": "gmail_send_email"})
    assert store.load_pending("a1")["tool"] == "gmail_send_email"
    store.delete_pending("a1")
    assert store.load_pending("a1") is None

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import create_app
from app.db import Base
from app.api.deps import get_db
from app.config import settings

@pytest.fixture
def client(tmp_path, monkeypatch):
    # Setup a temp sqlite file db per test session
    db_path = tmp_path / "test.db"
    test_db_url = f"sqlite:///{db_path}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def _get_db_override():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_post_and_get_flow(client, monkeypatch):
    payload = {
        "message_id": "msg-100",
        "session_id": "session-abc",
        "content": "Hola, como estas foo bar?",
        "timestamp": "2023-06-15T14:30:00Z",
        "sender": "system"
    }

    # Override banned words for test
    monkeypatch.setenv("NEQUI_BANNED_WORDS", "foo,bar")

    r = client.post("/api/messages", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["metadata"]["word_count"] > 0
    assert "*" in data["content"]  # sanitized

    # List without filter
    r2 = client.get("/api/messages/session-abc?limit=10&offset=0")
    assert r2.status_code == 200
    data2 = r2.json()["data"]
    assert len(data2) == 1
    assert data2[0]["message_id"] == "msg-100"

    # Duplicate message_id -> 409
    r3 = client.post("/api/messages", json=payload)
    assert r3.status_code == 409


def test_filter_by_sender(client):
    p1 = {
        "message_id": "m1",
        "session_id": "s1",
        "content": "hola",
        "timestamp": "2023-06-15T14:30:00Z",
        "sender": "user"
    }
    p2 = {**p1, "message_id": "m2", "sender": "system"}

    client.post("/api/messages", json=p1)
    client.post("/api/messages", json=p2)

    r = client.get("/api/messages/s1?sender=user")
    assert r.status_code == 200
    items = r.json()["data"]
    assert len(items) == 1
    assert items[0]["sender"] == "user"

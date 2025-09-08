import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.services.message_service import MessageService, ProcessingConfig, InvalidSenderError
from app.domain.schemas import MessageIn


@pytest.fixture
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_process_and_store_sanitizes_and_counts(db_session):
    service = MessageService(db=db_session, config=ProcessingConfig(banned_words=["malo"]))

    payload = MessageIn(
        message_id="msg-1",
        session_id="s1",
        content="un texto malo con palabra malo",
        timestamp=datetime.now(timezone.utc),
        sender="user",
    )

    out = service.process_and_store(payload)

    assert out.content.count("*") >= 4  # 'malo' -> '****'
    assert out.metadata.word_count == len(out.content.split())
    assert out.metadata.character_count == len(out.content)


def test_invalid_sender_raises(db_session):
    service = MessageService(db=db_session, config=ProcessingConfig(banned_words=[]))
    payload = MessageIn(
        message_id="msg-2",
        session_id="s1",
        content="hola",
        timestamp=datetime.now(timezone.utc),
        sender="user",
    )
    # First one ok
    service.process_and_store(payload)

    # Now try invalid sender via bypass (simulate wrong pydantic parsing scenario)
    payload2 = payload.model_copy(update={"message_id": "msg-3", "sender": "admin"})
    with pytest.raises(InvalidSenderError):
        service.process_and_store(payload2)

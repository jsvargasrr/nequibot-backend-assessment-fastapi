from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List
import re

from sqlalchemy.orm import Session

from ..domain.entities import Message as MessageEntity
from ..domain.schemas import MessageIn, MessageOut, MessageMetadata
from ..repositories.message_repository import MessageRepository, DuplicateMessageIdError


class InvalidSenderError(Exception):
    pass


@dataclass
class ProcessingConfig:
    banned_words: List[str]


class MessageService:
    def __init__(self, db: Session, config: ProcessingConfig):
        self.repo = MessageRepository(db)
        self.config = config
        # build regex pattern for banned words (word boundary, case-insensitive)
        escaped = [re.escape(w.strip()) for w in config.banned_words if w.strip()]
        self._ban_pattern = re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE) if escaped else None

    def _sanitize(self, text: str) -> str:
        if not self._ban_pattern:
            return text
        def repl(m):
            return "*" * len(m.group(0))
        return self._ban_pattern.sub(repl, text)

    def process_and_store(self, payload: MessageIn) -> MessageOut:
        # Validate sender (pydantic already restricts, but we keep explicit error mapping example)
        if payload.sender not in ("user", "system"):
            raise InvalidSenderError("sender must be 'user' or 'system'")

        sanitized = self._sanitize(payload.content)
        word_count = len(sanitized.split())
        char_count = len(sanitized)
        processed_at = datetime.now(timezone.utc)

        entity = MessageEntity(
            message_id=payload.message_id,
            session_id=payload.session_id,
            content=sanitized,
            timestamp=payload.timestamp,
            sender=payload.sender,
            word_count=word_count,
            character_count=char_count,
            processed_at=processed_at,
        )

        saved = self.repo.add(entity)

        return MessageOut(
            message_id=saved.message_id,
            session_id=saved.session_id,
            content=saved.content,
            timestamp=saved.timestamp,
            sender=saved.sender,
            metadata=MessageMetadata(
                word_count=saved.word_count,
                character_count=saved.character_count,
                processed_at=saved.processed_at,
            ),
        )

    def list_by_session(self, session_id: str, limit: int, offset: int, sender: str | None):
        messages = self.repo.list_by_session(session_id, limit, offset, sender)
        out: list[MessageOut] = []
        for m in messages:
            out.append(
                MessageOut(
                    message_id=m.message_id,
                    session_id=m.session_id,
                    content=m.content,
                    timestamp=m.timestamp,
                    sender=m.sender,
                    metadata=MessageMetadata(
                        word_count=m.word_count,
                        character_count=m.character_count,
                        processed_at=m.processed_at,
                    ),
                )
            )
        return out

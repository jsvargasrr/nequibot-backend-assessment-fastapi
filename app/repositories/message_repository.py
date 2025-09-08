from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError
from ..domain.entities import Message


class DuplicateMessageIdError(Exception):
    pass


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, msg: Message) -> Message:
        self.db.add(msg)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            # likely duplicate message_id
            raise DuplicateMessageIdError("message_id already exists") from e
        self.db.refresh(msg)
        return msg

    def list_by_session(self, session_id: str, limit: int = 50, offset: int = 0, sender: Optional[str] = None) -> List[Message]:
        stmt = select(Message).where(Message.session_id == session_id)
        if sender:
            stmt = stmt.where(Message.sender == sender)
        # newest first by timestamp then id
        stmt = stmt.order_by(desc(Message.timestamp), desc(Message.id)).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars())

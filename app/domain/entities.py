from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from ..db import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    session_id: Mapped[str] = mapped_column(String(100), index=True)
    content: Mapped[str] = mapped_column(String)
    timestamp: Mapped["datetime"] = mapped_column(DateTime(timezone=True), index=True)
    sender: Mapped[str] = mapped_column(String(16), index=True)

    word_count: Mapped[int] = mapped_column(Integer)
    character_count: Mapped[int] = mapped_column(Integer)
    processed_at: Mapped["datetime"] = mapped_column(DateTime(timezone=True))

    created_at: Mapped["datetime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

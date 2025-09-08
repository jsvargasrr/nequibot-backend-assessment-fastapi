from fastapi import Depends, Header, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict, deque

from ..db import SessionLocal
from ..config import settings
from ..services.message_service import MessageService, ProcessingConfig


# --- DB session dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Simple API key auth ---
def get_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if settings.api_key:
        if not x_api_key or x_api_key != settings.api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return x_api_key


# --- Very naive in-memory rate limiting ---
_window_hits: dict[str, deque] = defaultdict(deque)

def rate_limit(request: Request):
    if settings.rate_limit_per_min and settings.rate_limit_per_min > 0:
        identifier = request.headers.get("X-API-Key") or request.client.host
        window = _window_hits[identifier]
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        # drop old
        while window and window[0] < one_minute_ago:
            window.popleft()
        if len(window) >= settings.rate_limit_per_min:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        window.append(now)


# --- Service DI ---
def get_message_service(db: Session = Depends(get_db)) -> MessageService:
    banned = [w.strip() for w in settings.banned_words.split(",") if w.strip()]
    return MessageService(db=db, config=ProcessingConfig(banned_words=banned))

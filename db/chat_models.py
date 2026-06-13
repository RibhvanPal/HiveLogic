from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
)
import uuid
from datetime import datetime, UTC
from db.base import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String, primary_key=True)
    report_id = Column(String, nullable=False)
    ticker = Column(String(20))
    title = Column(String)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    session_id = Column(
        String,
        ForeignKey("chat_sessions.id"),
    )
    role = Column(String)
    content = Column(Text)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
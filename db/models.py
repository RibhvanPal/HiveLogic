import os
import uuid
from datetime import datetime,UTC
from dotenv import load_dotenv

load_dotenv()
from sqlalchemy import (
    create_engine, Column, String, Text, Float, Boolean,
    DateTime, JSON, Integer
)
from sqlalchemy.orm import sessionmaker
from db.base import Base
from db.chat_models import (
    ChatSession,
    ChatMessage,
)

# Use sqlite locally, PostgreSQL in production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/hivelogic.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

print("DATABASE_URL =", DATABASE_URL)
print("ENGINE URL =", engine.url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker = Column(String(20), index=True, nullable=False)
    query = Column(Text, nullable=False)
    final_report = Column(Text)
    financial_metrics = Column(JSON, default=dict)
    sentiment_label = Column(String(20))
    sentiment_score = Column(Float)
    verified = Column(Boolean, default=False)
    citations = Column(JSON, default=list)
    contagion_risks = Column(JSON, default=list)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

class Watchlist(Base):
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False)
    added_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    notes = Column(Text, default="")

def init_db():
    # create all tables
    import pathlib
    pathlib.Path("data").mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("[DB] Initialized.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
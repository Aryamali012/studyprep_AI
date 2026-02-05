from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from core.database import Base

class NoteSession(Base):
    __tablename__ = "note_sessions"

    id = Column(Integer, primary_key=True)
    topic = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class NoteMessage(Base):
    __tablename__ = "note_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer)
    role = Column(String)  # user / ai
    content = Column(Text)

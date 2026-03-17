"""
SQLAlchemy model for user notes.
Stored in the existing 'studyprep' MySQL database.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from core.database import Base


class UserNote(Base):
    __tablename__ = "user_notes"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String(36), nullable=False, index=True)   # matches users.user_id
    topic      = Column(String(500), nullable=False)
    content    = Column(Text, nullable=False)                     # generated notes text
    pdf_path   = Column(String(500), nullable=True)               # path to PDF file
    created_at = Column(DateTime, default=datetime.utcnow)

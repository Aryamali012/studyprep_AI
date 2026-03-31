from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base

class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True, nullable=False)
    exam_name = Column(String(255))
    start_date = Column(String(50))
    end_date = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship to Daily tasks
    tasks = relationship("DailyTask", back_populates="plan", cascade="all, delete-orphan")

class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id"))
    day_of_study = Column(Integer)
    date_str = Column(String(50))
    subject = Column(String(255))
    chapter = Column(String(255))
    focus_suggested = Column(String(500))
    is_completed = Column(Boolean, default=False)

    # Back reference to the plan
    plan = relationship("StudyPlan", back_populates="tasks")

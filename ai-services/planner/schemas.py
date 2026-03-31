from pydantic import BaseModel
from typing import List, Dict, Optional, Any

# Incoming request schema
class StudyPlanRequest(BaseModel):
    user_id: str
    startDate: str
    endDate: str
    exam: str
    gateBranch: Optional[str] = None
    subjects: Dict[str, List[str]]
    weekdayHours: float
    weekendHours: float
    chapterRatings: Dict[str, Dict[str, int]]
    emailReminders: bool

# Outgoing schemas (DB representations)
class DailyTaskResponse(BaseModel):
    id: int
    plan_id: int
    day_of_study: int
    date_str: str
    subject: str
    chapter: str
    focus_suggested: str
    is_completed: bool

    class Config:
        orm_mode = True

class StudyPlanResponse(BaseModel):
    id: int
    user_id: str
    exam_name: str
    start_date: str
    end_date: str
    tasks: List[DailyTaskResponse]

    class Config:
        orm_mode = True

from pydantic import BaseModel
from typing import List, Optional


class GenerateTestRequest(BaseModel):
    chapter_text: str
    subject: str = "Computer Science"
    num_mcq: int = 10
    num_subjective: int = 5
    difficulty: str = "Medium"  # Easy | Medium | Hard


class MCQQuestion(BaseModel):
    id: int
    type: str = "mcq"
    question: str
    options: List[str]          # Always 4 options
    correct_option: int         # 0-indexed
    marks: int                  # 1 or 2
    explanation: str


class SubjectiveQuestion(BaseModel):
    id: int
    type: str = "subjective"
    question: str
    expected_answer: str
    marks: int                  # 2 or 5


class TestResponse(BaseModel):
    subject: str
    difficulty: str
    total_marks: int
    duration_minutes: int
    mcq_questions: List[MCQQuestion]
    subjective_questions: List[SubjectiveQuestion]

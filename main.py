from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import GenerateTestRequest, TestResponse
from generator import generate_test
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="GATE Mock Test Generator API",
    description="Generates GATE-style MCQ and Subjective questions using Groq AI (Llama 3)",
    version="1.0.0",
)

# Allow frontend (file:// or localhost) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "GATE Mock Test Generator API is running!",
        "docs": "/docs",
    }


@app.post("/generate-test", response_model=TestResponse)
def generate_test_endpoint(request: GenerateTestRequest):
    if not request.chapter_text.strip():
        raise HTTPException(status_code=400, detail="chapter_text cannot be empty.")

    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not set. Please add it to backend/.env file.",
        )

    if request.num_mcq < 1 or request.num_mcq > 30:
        raise HTTPException(status_code=400, detail="num_mcq must be between 1 and 30.")

    if request.num_subjective < 0 or request.num_subjective > 15:
        raise HTTPException(status_code=400, detail="num_subjective must be between 0 and 15.")

    try:
        mcq_questions, subjective_questions = generate_test(
            chapter_text=request.chapter_text,
            subject=request.subject,
            num_mcq=request.num_mcq,
            num_subjective=request.num_subjective,
            difficulty=request.difficulty,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

    # Calculate total marks
    total_marks = sum(q.marks for q in mcq_questions) + sum(q.marks for q in subjective_questions)

    # Duration: ~1.5 min per mark, minimum 30 min
    duration_minutes = max(30, int(total_marks * 1.5))

    return TestResponse(
        subject=request.subject,
        difficulty=request.difficulty,
        total_marks=total_marks,
        duration_minutes=duration_minutes,
        mcq_questions=mcq_questions,
        subjective_questions=subjective_questions,
    )

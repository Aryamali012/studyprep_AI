from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import GenerateTestRequest, TestResponse   # ← EXISTING, unchanged
from generator import generate_test                    # ← EXISTING, unchanged
import os
from dotenv import load_dotenv

# New imports for result analysis
from app.database import engine
from app.models.db_models import Base
from app.routers import attempts, analytics, dashboard

load_dotenv()

# ---------------------------------------------------------------------------
# Auto-create new tables in MySQL (existing tables are NEVER touched)
# test_attempts, attempt_answers
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title       = "GATE Mock Test Generator & Result Analysis API",
    description = (
        "Generates GATE-style questions using Groq AI (Llama 3) "
        "and stores student test results with subject-wise analytics."
    ),
    version     = "2.0.0",
)

# CORS — keep same as before
app.add_middleware(
    CORSMiddleware,
    allow_origins      = ["*"],
    allow_credentials  = True,
    allow_methods      = ["*"],
    allow_headers      = ["*"],
)

# ---------------------------------------------------------------------------
# New routers
# ---------------------------------------------------------------------------
app.include_router(attempts.router,  prefix="/attempts",  tags=["Attempts"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])


# ---------------------------------------------------------------------------
# EXISTING endpoints — completely unchanged
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status":  "ok",
        "message": "GATE Mock Test Generator & Result Analysis API is running!",
        "docs":    "/docs",
        "version": "2.0.0",
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
            chapter_text    = request.chapter_text,
            subject         = request.subject,
            num_mcq         = request.num_mcq,
            num_subjective  = request.num_subjective,
            difficulty      = request.difficulty,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

    total_marks       = sum(q.marks for q in mcq_questions) + sum(q.marks for q in subjective_questions)
    duration_minutes  = max(30, int(total_marks * 1.5))

    return TestResponse(
        subject             = request.subject,
        difficulty          = request.difficulty,
        total_marks         = total_marks,
        duration_minutes    = duration_minutes,
        mcq_questions       = mcq_questions,
        subjective_questions= subjective_questions,
    )

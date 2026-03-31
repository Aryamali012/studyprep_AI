from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from schemas import StudyPlanRequest, StudyPlanResponse, DailyTaskResponse
import ai_service
from database import engine, get_db, Base
import models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="StudyPrep AI - Stateful Planner Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-plan", response_model=StudyPlanResponse)
def generate_plan(request: StudyPlanRequest, db: Session = Depends(get_db)):
    try:
        # Generate raw dict plans from Ollama
        raw_tasks = ai_service.generate_study_plan(request)
        
        # Invalidate old plans for this user (delete or just keep multiple, we'll keep only max 1 active plan for simplicity)
        old_plans = db.query(models.StudyPlan).filter(models.StudyPlan.user_id == request.user_id).all()
        for plan in old_plans:
            db.delete(plan)
        db.commit()

        # Save new study plan
        new_plan = models.StudyPlan(
            user_id=request.user_id,
            exam_name=request.exam,
            start_date=request.startDate,
            end_date=request.endDate
        )
        db.add(new_plan)
        db.flush() # flush to get new_plan.id

        # Save generated tasks
        saved_tasks = []
        for task_dict in raw_tasks:
            new_task = models.DailyTask(
                plan_id=new_plan.id,
                day_of_study=task_dict['day_of_study'],
                date_str=task_dict['date_str'],
                subject=task_dict['subject'],
                chapter=task_dict['chapter'],
                focus_suggested=task_dict['focus_suggested'],
                is_completed=False
            )
            db.add(new_task)
            saved_tasks.append(new_task)
            
        db.commit()
        db.refresh(new_plan)
        
        return new_plan

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/my-plan/{user_id}", response_model=StudyPlanResponse)
def get_user_plan(user_id: str, db: Session = Depends(get_db)):
    plan = db.query(models.StudyPlan).filter(models.StudyPlan.user_id == user_id).order_by(models.StudyPlan.id.desc()).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No active plan found for this user.")
    return plan

@app.post("/mark-complete/{task_id}")
def mark_task_complete(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.DailyTask).filter(models.DailyTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    
    task.is_completed = True
    db.commit()
    return {"message": "Task marked as completed", "status": "success", "task_id": task_id}

@app.get("/")
def read_root():
    return {"message": "StudyPrep AI Stateful Planner Service is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

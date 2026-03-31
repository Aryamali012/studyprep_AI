import os
import json
import requests
from dotenv import load_dotenv
from typing import List
from datetime import datetime, timedelta
from schemas import StudyPlanRequest

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

def generate_study_plan(request_data: StudyPlanRequest) -> List[dict]:
    start = datetime.strptime(request_data.startDate, "%Y-%m-%d")
    end = datetime.strptime(request_data.endDate, "%Y-%m-%d")
    days = (end - start).days + 1

    if days <= 0:
        days = 1

    # Extract all subjects and chapters to a flat list for prompt
    all_chapters = []
    for subj, chs in request_data.subjects.items():
        all_chapters.extend([f"{subj}: {c}" for c in chs])
    
    # Extract weak topics based on ratings (1 or 2 are considered weak)
    weak_topics = []
    for subj, ratings in request_data.chapterRatings.items():
        for ch, rating in ratings.items():
            if rating <= 2:
                weak_topics.append(f"{subj}: {ch}")

    prompt = f"""
You are an expert Study Planner. Create a {days}-day study plan based on the following context.
Exam: {request_data.exam}
Subjects and Chapters to cover: {', '.join(all_chapters)}
Weak Topics (Needs more focus): {', '.join(weak_topics) if weak_topics else 'None specified'}
Weekday Hours available daily: {request_data.weekdayHours}
Weekend Hours available daily: {request_data.weekendHours}

CRITICAL RULES:
1. Provide a day-by-day JSON array plan spreading the material over exactly {days} days.
2. If there are more chapters than available days ({days}), you MUST group multiple chapters together on a single day.
3. EVERY SINGLE subject and chapter listed above MUST be covered at least once in the plan. Do not leave any out.
4. Give priority and extra time allocations to weak topics. Be concise.

Provide the output STRICTLY as a JSON array of objects. Do not include markdown codeblocks like ```json, just output the raw JSON string array.
Each object must have exactly these keys:
- "date": string (format: YYYY-MM-DD, starting from {request_data.startDate} up to {request_data.endDate})
- "dayOfStudy": integer (from 1 to {days})
- "subject": string (the subject to study that day)
- "chapter": string (the specific chapter or topics, combine them if necessary)
- "focus_suggested": string (a short suggestion on what to focus on today)

JSON Array Output:
"""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a specialized JSON-generating planner machine."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        content = response.json().get("message", {}).get("content", "").strip()
        
        # Strip markdown formatting
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        plan_data = json.loads(content.strip())
        
        # Parse output to dicts
        tasks = []
        for item in plan_data:
            tasks.append({
                "date_str": item.get("date", ""),
                "day_of_study": item.get("dayOfStudy", 0),
                "subject": item.get("subject", ""),
                "chapter": item.get("chapter", ""),
                "focus_suggested": item.get("focus_suggested", "")
            })
        return tasks
    except Exception as e:
        print(f"Error generating plan: {e}")
        # Fallback to a simple 1-day plan
        return [
            {
                "date_str": request_data.startDate,
                "day_of_study": 1,
                "subject": "General",
                "chapter": "Review all material",
                "focus_suggested": "AI service unavailable. Please review topics naturally."
            }
        ]

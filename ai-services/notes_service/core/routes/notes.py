from fastapi import APIRouter
from pydantic import BaseModel
from core.services.notes_generator import generate_notes
from core.services.pdf_generator import generate_pdf

router = APIRouter()

class NotesRequest(BaseModel):
    topic: str

@router.post("/generate")
def generate_notes_api(data: NotesRequest):
    notes = generate_notes(data.topic)
    pdf_path = generate_pdf(notes, data.topic.replace(" ", "_"))
    return {
        "notes": notes,
        "pdf":f"http://127.0.0.1:8000/{pdf_path}"
    }

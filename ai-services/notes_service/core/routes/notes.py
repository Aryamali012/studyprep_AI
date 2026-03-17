"""
Notes API routes.
- POST /generate   — generate notes and save to DB
- GET  /history     — get all notes for a user
- GET  /{note_id}   — get a single note's full content
- DELETE /{note_id} — delete a note
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.models.notes import UserNote
from core.services.notes_generator import generate_notes
from core.services.pdf_generator import generate_pdf

router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class NotesRequest(BaseModel):
    topic: str
    user_id: str


class NoteOut(BaseModel):
    id: int
    topic: str
    created_at: str

    class Config:
        from_attributes = True


class NoteDetail(BaseModel):
    id: int
    topic: str
    content: str
    pdf_path: str | None
    created_at: str

    class Config:
        from_attributes = True


# ── Generate notes ────────────────────────────────────────────────────────────

@router.post("/generate")
def generate_notes_api(data: NotesRequest, db: Session = Depends(get_db)):
    # 1. Generate notes via LLM
    notes = generate_notes(data.topic)

    # 2. Generate PDF (Optional: if it fails, notes still save)
    pdf_path = None
    try:
        pdf_path = generate_pdf(notes, data.topic.replace(" ", "_"))
    except Exception as e:
        print(f"Failed to generate PDF: {e}")

    # 3. Save to database
    note = UserNote(
        user_id=data.user_id,
        topic=data.topic,
        content=notes,
        pdf_path=pdf_path,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        "id": note.id,
        "notes": notes,
        "pdf": pdf_path
    }


# ── Get history for a user ────────────────────────────────────────────────────

@router.get("/history")
def get_notes_history(user_id: str = Query(...), db: Session = Depends(get_db)):
    notes = (
        db.query(UserNote)
        .filter(UserNote.user_id == user_id)
        .order_by(UserNote.created_at.desc())
        .all()
    )
    return [
        {
            "id": n.id,
            "topic": n.topic,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for n in notes
    ]


# ── Get a single note ─────────────────────────────────────────────────────────

@router.get("/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(UserNote).filter(UserNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {
        "id": note.id,
        "topic": note.topic,
        "content": note.content,
        "pdf_path": note.pdf_path,
        "created_at": note.created_at.strftime("%Y-%m-%d %H:%M"),
    }


# ── Delete a note ─────────────────────────────────────────────────────────────

@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(UserNote).filter(UserNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"message": "Note deleted"}

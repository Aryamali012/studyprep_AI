from fastapi import FastAPI, APIRouter
from core.routes.notes import router as notes_router
from core.database import init_db
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Notes Generator Service")

# CORS must be added BEFORE routes so preflight OPTIONS requests are handled
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage", StaticFiles(directory="storage"), name="storage")

app.include_router(notes_router, prefix="/notes")

# Create tables on startup
init_db()

@app.get("/")
def health():
    return {"status": "Notes service running"}

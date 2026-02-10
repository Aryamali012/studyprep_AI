from fastapi import FastAPI
from fastapi import UploadFile, File
from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
from utils.ocr import extract_text_from_pdf
from utils.parser import split_questions

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Question Solver Backend Running"}


app = FastAPI()

UPLOAD_DIR = "tmp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/extract-pdf-text")
async def extract_pdf_text(file: UploadFile = File(...), lang: str = "eng"):
    # basic validation
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")
    tmp_path = os.path.join(UPLOAD_DIR, file.filename)
    # save uploaded file
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        text = extract_text_from_pdf(tmp_path, lang=lang)
    finally:
        # optional: remove file to keep disk clean
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    return {"filename": file.filename, "text": text}

@app.post("/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    tmp_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = extract_text_from_pdf(tmp_path)
    questions = split_questions(text)

    os.remove(tmp_path)

    return {"total_questions": len(questions), "questions": questions}

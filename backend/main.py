# backend/main.py
import os
import re
import shutil
import tempfile
import time
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse

# Groq client
from groq import Groq

# utilities you already have
from utils.ocr import extract_text_from_pdf
from utils.parser import split_questions

# ReportLab / platypus for nice PDF layout
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, KeepTogether
from reportlab.lib.units import inch

app = FastAPI(title="Question Paper Solver (Groq)")

# --- GROQ client init (expects env var GROQ_API_KEY) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not set. Set GROQ_API_KEY env var to call Groq API.")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


@app.get("/")
def root():
    return {"message": "Backend running"}


# --- Helper: Ask Groq in batch with strict markers and parse answers ---
def ask_groq_batch_and_parse(questions: List[str], model: str = "llama-3.3-70b-versatile") -> List[str]:
    """
    Sends a batch of questions and asks the model to return answers using explicit markers:
    <<<Q1>>> ... <<<ENDQ1>>>
    Returns list of answers aligned with questions.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Groq client not configured (GROQ_API_KEY missing).")

    # Build prompt with strong instruction for markers
    lines = [
        "You are an expert exam tutor. For each numbered question below produce a concise exam-style answer.",
        "IMPORTANT: For question i (1-based), START the answer block with <<<Qi>>> on its own line",
        "and END the block with <<<ENDQi>>> on its own line. Use exactly these markers and nothing else to separate answers.",
        "Do NOT include commentary outside the markers. Provide the answer text only between markers.",
        ""
    ]
    for idx, q in enumerate(questions, start=1):
        lines.append(f"Question {idx}:\n{q}\n")
    prompt = "\n".join(lines)

    # Call Groq chat completion
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=2000
        )
        resp_text = completion.choices[0].message.content
    except Exception as e:
        # Let caller handle it / log
        raise

    # Debug preview
    print("LLM raw response preview:", (resp_text or "")[:800].replace("\n", " "))

    # Parse markers
    pattern = re.compile(r'<<<Q(\d+)>>>(.*?)<<<ENDQ\1>>>', re.S)
    matches = pattern.findall(resp_text or "")

    answers = ["" for _ in questions]
    if matches:
        for num_str, body in matches:
            try:
                num = int(num_str)
                if 1 <= num <= len(questions):
                    answers[num - 1] = body.strip()
            except ValueError:
                continue
    else:
        # fallback: try splitting by "Question 1:", "Question 2:"...
        fallback = []
        for i in range(1, len(questions) + 1):
            p = re.compile(rf'(?:Question\s*{i}\s*:)(.*?)(?=(?:Question\s*{i+1}\s*:)|\Z)', re.S)
            m = p.search(resp_text or "")
            if m:
                fallback.append(m.group(1).strip())
            else:
                fallback.append("")
        answers = fallback

    # final safety: fill empties with coarse splits if needed
    for idx, a in enumerate(answers):
        if not a:
            parts = [p.strip() for p in (resp_text or "").split("\n\n") if p.strip()]
            if idx < len(parts):
                answers[idx] = parts[idx]
            else:
                answers[idx] = ""

    return answers


# --- PDF creator: question bold, "Answer:" label, KeepTogether to avoid page-splits ---
def create_pdf(qna_pairs: List[tuple], out_path: str, font_name: str = "Helvetica"):
    """
    qna_pairs: list of (question_text, answer_text)
    Produces a readable PDF where question is bold, then "Answer:" label, then answer body.
    """
    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()

    q_style = ParagraphStyle(
        "QuestionStyle",
        parent=styles["Normal"],
        fontName=f"{font_name}-Bold" if font_name != "Helvetica" else "Helvetica-Bold",
        fontSize=12,
        leading=16,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontName=f"{font_name}-Bold" if font_name != "Helvetica" else "Helvetica-Bold",
        fontSize=11,
        leading=14,
        spaceAfter=2,
        alignment=TA_LEFT
    )
    a_style = ParagraphStyle(
        "AnswerStyle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=14,
        spaceAfter=12,
        alignment=TA_LEFT
    )

    flowables = []
    for idx, (qtext, atext) in enumerate(qna_pairs, start=1):
        # sanitize & convert newlines to <br/>
        safe_q = qtext.replace("<", "&lt;").replace(">", "&gt;").replace("\r", "").replace("\n", "<br/>")
        safe_a = atext.replace("<", "&lt;").replace(">", "&gt;").replace("\r", "").replace("\n", "<br/>")

        # Build block and keep together so Q and its Answer don't split across pages
        block = []
        block.append(Paragraph(f"<b>Q{idx}:</b> {safe_q}", q_style))
        block.append(Spacer(1, 6))
        block.append(Paragraph("Answer:", label_style))
        block.append(Paragraph(safe_a or "[No answer provided]", a_style))
        # separator line
        block.append(Spacer(1, 6))
        block.append(Paragraph("<br/>" + "-" * 90, styles["Normal"]))
        block.append(Spacer(1, 10))

        flowables.append(KeepTogether(block))

    doc.build(flowables)


# --- Main endpoint: upload PDF -> answers PDF ---
@app.post("/solve-pdf")
async def solve_pdf(
    file: UploadFile = File(...),
    model: str = Query("llama-3.3-70b-versatile"),
    batch_size: int = Query(5, ge=1, le=20)
):
    """
    Upload a PDF -> returns answers PDF.
    Query params:
      - model: Groq model name (default recommended model)
      - batch_size: questions per API call (default 5)
    """
    if not client:
        raise HTTPException(status_code=500, detail="GROQ API key not configured. Set GROQ_API_KEY env var.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    tmp_dir = tempfile.mkdtemp(prefix="qs_")
    pdf_path = os.path.join(tmp_dir, file.filename)

    # Save upload
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    print("Saved uploaded PDF:", pdf_path)

    # Extract text (our util handles selectable/scanned)
    try:
        extracted_text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {e}")

    if not extracted_text or not extracted_text.strip():
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="No text extracted from PDF. Use a legible PDF or scanned image.")

    # Parse into questions
    questions = split_questions(extracted_text)
    if not questions:
        questions = [extracted_text.strip()]

    print("Parsed questions count:", len(questions))

    # Build Q-A pairs with batching
    qna_pairs = []
    for start in range(0, len(questions), batch_size):
        batch_questions = questions[start:start + batch_size]
        attempt = 0
        max_attempts = 2
        answers = None
        while attempt < max_attempts:
            try:
                answers = ask_groq_batch_and_parse(batch_questions, model=model)
                break
            except Exception as e:
                attempt += 1
                print(f"Groq call failed (attempt {attempt}): {e}")
                time.sleep(3)
        if answers is None:
            # persistent failure -> placeholder answers
            answers = ["[Error calling model]" for _ in batch_questions]

        for q_text, ans_text in zip(batch_questions, answers):
            cleaned = re.sub(r'^\s*Answer\s*[:\-]?\s*', '', (ans_text or "").strip(), flags=re.I)
            qna_pairs.append((q_text.strip(), cleaned.strip()))

    # Create output PDF
    out_pdf = os.path.join(tmp_dir, f"answers_{int(time.time())}.pdf")
    try:
        create_pdf(qna_pairs, out_pdf)
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    # Respond with file
    return FileResponse(out_pdf, filename=os.path.basename(out_pdf), media_type="application/pdf")

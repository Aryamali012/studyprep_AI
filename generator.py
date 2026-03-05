import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from models import MCQQuestion, SubjectiveQuestion

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an expert GATE exam question setter with 15+ years of experience.
Your task is to generate high-quality GATE-style questions based on the given chapter/topic content.

GATE exam rules:
- MCQ 1-mark: 4 options (A-D), one correct, negative marking -1/3
- MCQ 2-mark: 4 options (A-D), one correct, negative marking -2/3
- Subjective (NAT / Short Answer): numerical or descriptive answer

Always generate questions that test:
- Conceptual understanding
- Application of theory
- Problem-solving ability
- Analytical thinking

You MUST respond ONLY with valid JSON, no extra text or markdown fences."""


def build_prompt(chapter_text: str, subject: str, num_mcq: int, num_subjective: int, difficulty: str) -> str:
    return f"""Generate a GATE mock test from the following chapter content.

Chapter/Topic Content:
\"\"\"
{chapter_text}
\"\"\"

Requirements:
- Subject: {subject}
- Difficulty: {difficulty}
- Number of MCQ questions: {num_mcq} (mix of 1-mark and 2-mark)
- Number of Subjective questions: {num_subjective} (mix of 2-mark and 5-mark)

Return ONLY a valid JSON object with this exact structure:
{{
  "mcq_questions": [
    {{
      "id": 1,
      "type": "mcq",
      "question": "Question text here?",
      "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
      "correct_option": 0,
      "marks": 1,
      "explanation": "Brief explanation of why the answer is correct"
    }}
  ],
  "subjective_questions": [
    {{
      "id": 1,
      "type": "subjective",
      "question": "Subjective question text here?",
      "expected_answer": "Detailed expected answer / solution",
      "marks": 2
    }}
  ]
}}

Rules:
- correct_option is 0-indexed (0=A, 1=B, 2=C, 3=D)
- marks for MCQ: 1 or 2 only
- marks for subjective: 2 or 5 only
- All questions must be strictly based on the provided chapter content
- Questions must be relevant to GATE {subject} syllabus
- Difficulty: {difficulty} — {"Easy questions test basic recall and simple application." if difficulty=="Easy" else "Medium questions require moderate conceptual depth and some calculations." if difficulty=="Medium" else "Hard questions require deep understanding, multi-step reasoning, and complex problem solving."}
- Generate exactly {num_mcq} MCQ and {num_subjective} subjective questions
"""


def extract_json(text: str) -> dict:
    """Extract JSON from response even if there's surrounding text."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON block from markdown fences
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding raw JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract valid JSON from model response")


def generate_test(chapter_text: str, subject: str, num_mcq: int, num_subjective: int, difficulty: str):
    prompt = build_prompt(chapter_text, subject, num_mcq, num_subjective, difficulty)

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=8000,
        response_format={"type": "json_object"},
    )

    raw = chat_completion.choices[0].message.content
    data = extract_json(raw)

    mcq_list = []
    for i, q in enumerate(data.get("mcq_questions", [])):
        mcq_list.append(MCQQuestion(
            id=i + 1,
            type="mcq",
            question=q["question"],
            options=q["options"],
            correct_option=q["correct_option"],
            marks=q.get("marks", 1),
            explanation=q.get("explanation", ""),
        ))

    subj_list = []
    for i, q in enumerate(data.get("subjective_questions", [])):
        subj_list.append(SubjectiveQuestion(
            id=i + 1,
            type="subjective",
            question=q["question"],
            expected_answer=q.get("expected_answer", ""),
            marks=q.get("marks", 2),
        ))

    return mcq_list, subj_list

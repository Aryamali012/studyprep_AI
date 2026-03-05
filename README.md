# ⚡ GATE Mock Test Generator — Backend API

An AI-powered GATE exam mock test generator using **FastAPI** + **Groq (Llama 3.3-70b)**. Send chapter content, get GATE-style MCQ + Subjective questions back as JSON.

---

## 🚀 Quick Start

### 1. Get a Free Groq API Key
1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up (free) → **API Keys** → **Create New Key**
3. Copy your key

### 2. Add the Key to `.env`
Edit `backend/.env`:
```
GROQ_API_KEY=gsk_your_key_here
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Start the Server
```bash
uvicorn main:app --reload
```

The API is now live at `http://localhost:8000`

---

## 📡 API Endpoints

### `GET /`
Health check.

### `POST /generate-test`
Generate a GATE mock test from chapter content.

**Request Body:**
```json
{
  "chapter_text": "Binary Trees, BST, AVL Trees, Tree traversals...",
  "subject": "Computer Science",
  "num_mcq": 10,
  "num_subjective": 5,
  "difficulty": "Medium"
}
```

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `chapter_text` | string | — | Any chapter notes / topic list |
| `subject` | string | `"Computer Science"` | CS, ECE, EE, ME, CE, Engineering Mathematics, General Aptitude |
| `num_mcq` | int | `10` | 1–30 |
| `num_subjective` | int | `5` | 0–15 |
| `difficulty` | string | `"Medium"` | `Easy`, `Medium`, `Hard` |

**Response:**
```json
{
  "subject": "Computer Science",
  "difficulty": "Medium",
  "total_marks": 25,
  "duration_minutes": 37,
  "mcq_questions": [
    {
      "id": 1,
      "type": "mcq",
      "question": "Which traversal of a BST gives nodes in sorted order?",
      "options": ["Preorder", "Inorder", "Postorder", "Level-order"],
      "correct_option": 1,
      "marks": 1,
      "explanation": "Inorder traversal of a BST visits nodes in ascending order."
    }
  ],
  "subjective_questions": [
    {
      "id": 1,
      "type": "subjective",
      "question": "Explain the rotation operations in an AVL tree.",
      "expected_answer": "AVL trees use four rotations...",
      "marks": 5
    }
  ]
}
```

---

## 📖 Interactive API Docs
Once the server is running, visit:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🏗️ Project Structure
```
gate mock test generator/
└── backend/
    ├── main.py          # FastAPI app — routes & CORS
    ├── generator.py     # Groq AI integration & prompt building
    ├── models.py        # Pydantic request/response schemas
    ├── requirements.txt # Python dependencies
    ├── .env             # Your Groq API key (never commit this!)
    └── README.md        # This file
```

---

## ⚙️ GATE Marking Scheme (built into response)
| Question Type | Marks | Negative Marking |
|--------------|-------|-----------------|
| MCQ 1-mark   | +1    | −1/3 for wrong  |
| MCQ 2-mark   | +2    | −2/3 for wrong  |
| Subjective 2-mark | +2 | No negative    |
| Subjective 5-mark | +5 | No negative    |

"""
LLM client using local Ollama REST API.
"""

import os
import re
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")


def _strip_think_tags(text: str) -> str:
    """Remove <tool_call>...<tool_call> reasoning blocks if present."""
    return re.sub(r"<tool_call>.*?<tool_call>", "", text, flags=re.DOTALL).strip()


def _check_ollama_running() -> bool:
    """Ping Ollama's /api/tags endpoint to confirm it is reachable."""
    base_url = OLLAMA_URL.replace("/api/chat", "")
    ping_url = f"{base_url}/api/tags"
    try:
        with urllib.request.urlopen(ping_url, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def _check_model_available() -> bool:
    """Check whether the configured model is already pulled."""
    base_url = OLLAMA_URL.replace("/api/chat", "")
    tags_url = f"{base_url}/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            # Match either exact name or name without tag
            return any(
                OLLAMA_MODEL == m or OLLAMA_MODEL.split(":")[0] == m.split(":")[0]
                for m in models
            )
    except Exception:
        return False


def call_llm(prompt: str) -> str:
    """
    Generate text using the local Ollama model.
    Raises a clear RuntimeError on any connectivity or model issue.
    """

    # ── Pre-flight checks ────────────────────────────────────────────────────
    if not _check_ollama_running():
        raise RuntimeError(
            f"[LLM] Ollama is NOT reachable at '{OLLAMA_URL}'.\n"
            "  • Make sure Ollama is running:  ollama serve\n"
            "  • Confirm the port is correct in your .env:  OLLAMA_URL=http://localhost:11434/api/chat\n"
            "  • If running inside Docker, use the host IP instead of localhost."
        )

    if not _check_model_available():
        raise RuntimeError(
            f"[LLM] Model '{OLLAMA_MODEL}' is not pulled yet.\n"
            f"  Run:  ollama pull {OLLAMA_MODEL}"
        )

    # ── Build request ────────────────────────────────────────────────────────
    system_prompt = (
        "You are an expert teacher. Generate detailed, structured, "
        "long-form study notes. Use clear headings and subheadings. "
        "Do NOT include any reasoning or thinking process in your response."
    )

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.5,
            "top_p": 0.9,
        },
    }

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    # ── Call Ollama ──────────────────────────────────────────────────────────
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result  = json.loads(response.read().decode("utf-8"))
            content = result.get("message", {}).get("content", "")
            if not content:
                raise RuntimeError("[LLM] Ollama returned an empty response.")
            return _strip_think_tags(content)

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"[LLM] Ollama HTTP {e.code}: {e.reason}\n"
            f"  Response body: {body}"
        ) from e

    except urllib.error.URLError as e:
        raise RuntimeError(
            f"[LLM] Could not connect to Ollama at '{OLLAMA_URL}'.\n"
            f"  Reason: {e.reason}\n"
            "  Make sure Ollama is running and the URL in .env is correct."
        ) from e

    except TimeoutError:
        raise RuntimeError(
            "[LLM] Ollama timed out after 120 s. "
            "The model may be too large for your machine — try a smaller model."
        )
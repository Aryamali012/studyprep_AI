from fastapi import HTTPException
from core.services.llm_client import call_llm


def generate_notes(topic: str, level: str = "exam") -> str:
    prompt = (
        f'Generate VERY DETAILED study notes on the topic: "{topic}"\n\n'
        "Requirements:\n"
        "- Use headings and subheadings\n"
        "- Explain concepts in simple language\n"
        "- Give real-world examples\n"
        "- Do NOT summarize\n"
        "- Do NOT stop early\n"
        "- Cover the topic completely as if for exam preparation"
    )

    try:
        return call_llm(prompt)
    except RuntimeError as e:
        # Surface the diagnostic message directly in the API response
        raise HTTPException(status_code=503, detail=str(e))

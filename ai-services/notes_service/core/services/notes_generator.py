from core.services.gorq_client import call_llm

def generate_notes(topic, level="exam"):
    prompt = f"""
    Generate VERY DETAILED study notes on the topic: "{topic}"

    Requirements:
    - Use headings and subheadings
    - Explain concepts in simple language
    - Give real-world examples
    - Do NOT summarize
    - Do NOT stop early
    - Cover the topic completely as if for exam preparation
    """

    return call_llm(prompt)

from core.services.gorq_client import call_llm

def generate_notes(topic, level="exam"):
    prompt = f"""
    Generate VERY DETAILED study notes on the topic: "{topic}"

        Rules :
        1. Use headings and subheadings
        2. Use short paragraphs
        3. Use bullet points where applicable
        4. Keep language simple
        5. Use this format strictly:
        # Title
        ## Definition
        ## Explanation
        ## Properties
        - point
        - point
        ## Example
        ## Applications """

    return call_llm(prompt)

import re

def split_questions(text: str):
    """
    Split text into individual questions based on Q. pattern
    """
    pattern = r"(Q\.\s*\d+.*?)((?=Q\.\s*\d+)|$)"
    matches = re.findall(pattern, text, re.DOTALL)

    questions = []
    for match in matches:
        question_text = match[0].strip()
        questions.append(question_text)

    return questions

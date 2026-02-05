import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(prompt: str):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",   # or the model you fixed earlier
        messages=[
            {
                "role": "system",
                "content": "You are an expert teacher. Generate detailed, structured, long-form study notes."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=3000,   # 🔥 THIS IS THE KEY
        temperature=0.5
    )

    return response.choices[0].message.content

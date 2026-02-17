# test_groq.py
import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Please set GROQ_API_KEY environment variable before running this test.")
    raise SystemExit(1)

client = Groq(api_key=GROQ_API_KEY)

resp = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Explain stack in 2 lines."}],
    temperature=0.0,
    max_tokens=200
)

print("Response:\n")
print(resp.choices[0].message.content)

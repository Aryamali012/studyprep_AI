import os
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("HF_MODEL", "google/flan-t5-large")  # lightweight default

print(f"Loading model: {MODEL_NAME} ...")

# For CPU-friendly models like flan-t5
generator = pipeline(
    "text2text-generation",   # use "text-generation" for GPT-style models
    model=MODEL_NAME,
    device=0 if torch.cuda.is_available() else -1  # auto GPU/CPU
)

def call_llm(prompt: str) -> str:
    result = generator(
        prompt,
        max_new_tokens=2000,
        do_sample=True,
        temperature=0.5
    )
    return result[0]["generated_text"]
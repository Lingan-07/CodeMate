import requests
import numpy as np
import json
import dotenv
import os

dotenv.load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

EMBED_MODEL = "llama-3.1-8b-instant"

def get_embedding(text: str):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": EMBED_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return ONLY a JSON list of 128 floating point numbers. "
                    "No sentences. No explanations. Only raw JSON array.\n"
                    "Example: [0.12, -0.33, 1.55, ...]"
                )
            },
            {"role": "user", "content": f"Generate an embedding for:\n{text}"}
        ],
        "temperature": 0
    }

    res = requests.post(API_URL, headers=headers, json=body)

    if res.status_code != 200:
        print("Embedding error:", res.text)
        return None

    raw = res.json()["choices"][0]["message"]["content"].strip()

    try:
        vector = json.loads(raw)  # Force JSON parse

        # Ensure numeric list
        vector = [float(x) for x in vector]

        return vector
    except:
        print("❌ Failed to parse embedding:", raw)
        return None

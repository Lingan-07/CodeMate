# utils/summarize.py

import requests
import json
import dotenv
import os

dotenv.load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

API_URL = "https://api.groq.com/openai/v1/chat/completions"

def summarize_code(filename, code):
    prompt = f"""
You are an expert senior software engineer.
Summarize the following JavaScript file in a clear, concise way.

Focus on:
- Purpose of the file
- Key functions and what they do
- Important logic
- API calls or services involved
- How this file fits into the system

Return summary in bullet points.

FILENAME: {filename}

CODE:
{code}
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a code analysis expert."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    res = requests.post(API_URL, headers=headers, json=body)

    if res.status_code != 200:
        return f"Error from Groq: {res.text}"

    data = res.json()
    summary = data["choices"][0]["message"]["content"]
    return summary

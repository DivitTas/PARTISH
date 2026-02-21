import google.generativeai as genai
import json
from pydantic import ValidationError
from dotenv import load_dotenv
import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config={
        "response_mime_type": "application/json",
    }
)

SYSTEM_PROMPT = """
You are an email analysis engine.
Only return valid JSON.
Do not include explanations.
If a field is unknown, return null.
"""

def analyze_email(email_body: str):

    prompt = f"""
{SYSTEM_PROMPT}

Analyze the email below and return JSON with fields:
tone, deadline_hours, action_required,
sender_role, priority_score, summary, confidence.

Email:
\"\"\"
{email_body}
\"\"\"
"""

    response = model.generate_content(prompt)

    raw_json = response.text
    parsed = json.loads(raw_json)

    return EmailAnalysis(**parsed)

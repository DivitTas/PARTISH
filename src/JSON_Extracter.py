import google.generativeai as genai
import json
from pydantic import BaseModel, ValidationError
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class EmailAnalysis(BaseModel):
    tone: Optional[str] = None
    deadline_hours: Optional[int] = None
    action_required: bool
    sender_role: Optional[str] = None
    summary: str
    confidence: float

model = genai.GenerativeModel(
    model_name="gemini-flash-latest",
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
sender_role, summary, confidence.

Email:
\"\"\"
{email_body}
\"\"\"
"""

    try:
        response = model.generate_content(prompt)
        raw_json = response.text
        parsed = json.loads(raw_json)
        return EmailAnalysis(**parsed)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Error parsing model response: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

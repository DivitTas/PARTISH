from google import genai
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize the new Google GenAI client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class EmailAnalysis(BaseModel):
    tone: Optional[str] = None
    deadline_hours: Optional[int] = None
    action_required: bool
    sender_role: Optional[str] = None
    summary: str
    confidence: float

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
        # Use the new SDK's generate_content with response_schema for direct parsing
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": EmailAnalysis,
            }
        )
        return response.parsed
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

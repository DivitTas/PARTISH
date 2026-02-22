from src.JSON_Extracter import analyze_email_sentiment
import json
import os
import email # To parse raw email content
from email.header import decode_header # To decode email subject
import re # Added to fix NameError

# Ensure models are trained and available
MODEL_PATH = 'models/urgency_model.pkl'
VECTORIZER_PATH = 'models/vectorizer.pkl'

if not (os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH)):
    print("Warning: Trained models not found. Please run src/DecisionTree_Trainer.py first to train the model.")
    print("Proceeding with rule-based analysis only (no ML predictions).")

# --- Raw Email Content from User ---
raw_email_content = """Date: Tue, 21 Oct 2025 10:50
From: Sender Name <sender@example.com>
Reply-To: sender@example.com
To: recipient@example.com
Subject: Example Subject - Urgent Action Required
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: quoted-printable

Dear User,

This is an example email body. Please complete the required action by the deadline.

The deadline is tomorrow at 5pm.

Kind regards,
Sender Team
"""

def parse_raw_email(raw_email: str) -> tuple[str, str]:
    """
    Parses a raw email string to extract the subject and plain text body.
    """
    msg = email.message_from_string(raw_email)
    
    # Decode Subject
    decoded_subject = decode_header(msg['Subject'])
    subject = ''
    for s, charset in decoded_subject:
        if isinstance(s, bytes):
            subject += s.decode(charset if charset else 'utf-8', errors='ignore')
        else:
            subject += s

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))

            # Look for plain text parts that are not attachments
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    # Decode payload, handling quoted-printable
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset()
                    body = payload.decode(charset if charset else 'utf-8', errors='ignore')
                    break # Take the first plain text part
                except Exception as e:
                    print(f"Error decoding text part: {e}")
                    body = part.get_payload(decode=False) # Fallback
    else:
        # Not multipart, assume it's a plain text email
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset()
            body = payload.decode(charset if charset else 'utf-8', errors='ignore')
        except Exception as e:
            print(f"Error decoding single part email: {e}")
            body = msg.get_payload(decode=False) # Fallback

    # Clean up common email artifacts (e.g., encoded HTML/URLs if any slipped through)
    # This is a basic cleanup; more robust cleaning might be needed for real-world scenarios
    body = re.sub(r'=\w{2}', '', body) # Remove quoted-printable artifacts like =E2=80=99
    body = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', body) # Replace URLs
    body = re.sub(r'\s+', ' ', body).strip() # Reduce multiple spaces to single space

    return subject, body

# Parse the raw email content
my_email_subject, my_email_body = parse_raw_email(raw_email_content)

# Combine subject and body for analysis, as the model was trained on both.
email_to_analyze = my_email_subject + " " + my_email_body

print(f"Analyzing email with subject: '{my_email_subject}'")

# Run the analysis
analysis_result = analyze_email_sentiment(email_to_analyze)

# Print the results in a readable JSON format
print("\n--- Analysis Result ---")
print(json.dumps(analysis_result.dict(), indent=2))

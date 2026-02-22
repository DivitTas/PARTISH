from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
import base64
import os

from database import conn, cursor

# ---------------- LOAD ENV ----------------

load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
REDIRECT_URI = "http://localhost:8000/auth/callback"

app = FastAPI()

# =====================================================
# STEP 1 — START GMAIL AUTH
# =====================================================

@app.get("/auth/gmail")
def auth_gmail():

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent"  # forces refresh token
    )

    return RedirectResponse(auth_url)


# =====================================================
# STEP 2 — GOOGLE CALLBACK
# =====================================================

@app.get("/auth/callback")
def auth_callback(code: str, state: str):

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    flow.fetch_token(code=code)
    creds = flow.credentials

    gmail_service = build("gmail", "v1", credentials=creds)
    profile = gmail_service.users().getProfile(userId="me").execute()

    gmail_email = profile["emailAddress"]
    user_id = state

    print("Saving user:", user_id, gmail_email)

    cursor.execute(
        """
        INSERT OR REPLACE INTO gmail_tokens
        (user_id, gmail_email, refresh_token)
        VALUES (?, ?, ?)
        """,
        (user_id, gmail_email, creds.refresh_token),
    )

    conn.commit()
    print("callback done")
    return {"message": f"Gmail connected for {gmail_email}"}

# =====================================================
# LOAD TOKEN FROM DATABASE
# =====================================================

def get_gmail_service(user_id):

    cursor.execute(
        "SELECT refresh_token FROM gmail_tokens WHERE user_id=?",
        (user_id,),
    )

    row = cursor.fetchone()

    if not row:
        print("❌ No token found in DB")
        return None

    refresh_token = row[0]

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES,
    )

    return build("gmail", "v1", credentials=creds)


# =====================================================
# EMAIL PARSING
# =====================================================

def get_email_details(service, msg_id):

    message = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full"
    ).execute()

    headers = message["payload"]["headers"]

    subject = ""
    sender = ""

    for header in headers:
        if header["name"] == "Subject":
            subject = header["value"]
        if header["name"] == "From":
            sender = header["value"]

    body = ""

    parts = message["payload"].get("parts")

    if parts:
        for part in parts:
            if part["mimeType"] == "text/plain" and part["body"].get("data"):
                body = base64.urlsafe_b64decode(
                    part["body"]["data"]
                ).decode("utf-8")
                break

    return sender, subject, body


# =====================================================
# READ EMAILS ENDPOINT
# =====================================================

@app.get("/emails")
def read_emails():

    user_id = "demo_user"

    service = get_gmail_service(user_id)

    if not service:
        return {"error": "Gmail not connected"}

    results = service.users().messages().list(
        userId="me",
        maxResults=5
    ).execute()

    messages = results.get("messages", [])

    emails = []

    for msg in messages:
        sender, subject, body = get_email_details(service, msg["id"])

        emails.append({
            "from": sender,
            "subject": subject,
            "body": body[:200],
        })

    return emails
from __future__ import print_function
import os.path
import base64
from dotenv import load_dotenv
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle

# Permission scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

def authenticate_gmail():
    creds = None

    # token.pickle stores login session
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If not logged in → open Google login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:8080/"]
                    }
                },
            SCOPES,
            )
            creds = flow.run_local_server(port=8080)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def get_email_details(service, msg_id):
    message = service.users().messages().get(
        userId='me',
        id=msg_id,
        format='full'
    ).execute()

    headers = message['payload']['headers']

    subject = ""
    sender = ""

    for header in headers:
        if header['name'] == 'Subject':
            subject = header['value']
        if header['name'] == 'From':
            sender = header['value']

    body = ""

    parts = message['payload'].get('parts')

    if parts:
        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                break
    else:
        data = message['payload']['body'].get('data')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8')

    return sender, subject, body

def read_emails():
    creds = authenticate_gmail()

    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(
        userId='me',
        maxResults=5
    ).execute()

    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
        return

    for msg in messages:
        sender, subject, body = get_email_details(service, msg['id'])

        print("\n-------------------")
        print("From:", sender)
        print("Subject:", subject)
        print("Body:", body[:200])


if __name__ == '__main__':
    read_emails()
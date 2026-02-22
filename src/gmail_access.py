from __future__ import print_function
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials # Import Credentials class
from google.auth.transport.requests import Request as GoogleAuthRequest

# Permission scope (ensure these match the scopes requested in app/routers/auth.py)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service(credentials: Credentials):
    """
    Returns a Google Gmail API service object using provided credentials.
    """
    if not credentials or not credentials.valid:
        raise ValueError("Invalid or expired Google credentials provided.")
    
    # Refresh token if expired
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleAuthRequest()) # Needs Request from google.auth.transport.requests

    service = build('gmail', 'v1', credentials=credentials)
    return service

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
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from app.routers.auth import get_google_credentials
from src.gmail_access import get_gmail_service, get_email_details

router = APIRouter()

@router.get("/messages", response_model=List[Dict])
async def list_gmail_messages(credentials: Credentials = Depends(get_google_credentials)):
    """
    Fetches a list of recent Gmail messages for the authenticated user.
    """
    try:
        gmail_service = get_gmail_service(credentials)
        
        # Fetch up to 5 messages. Adjust maxResults or add 'q' for specific queries.
        results = gmail_service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages:
            return []

        messages_data = []
        for msg_obj in messages:
            msg_id = msg_obj['id']
            sender, subject, body = get_email_details(gmail_service, msg_id)
            messages_data.append({
                "id": msg_id,
                "sender": sender,
                "subject": subject,
                "body_preview": body[:200]
            })
        return messages_data

    except HttpError as error:
        raise HTTPException(status_code=error.resp.status, detail=f"Gmail API error: {error.content.decode()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

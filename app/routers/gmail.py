from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from app.routers.auth import get_google_credentials
from src.gmail_access import get_gmail_service, get_email_details
from src.JSON_Extracter import analyze_email_sentiment
from src.date_parser import parse_deadline_string
from src.calendar_api import get_calendar_service, create_calendar_event # Import Calendar API functions

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

# Background task function (to keep the API response fast)
async def _process_email_background(
    email_text: str,
    email_subject: str,
    email_sender: str,
    gmail_credentials: Credentials,
    calendar_credentials: Credentials # Re-added
):
    """
    Processes a single email for urgency and creates a calendar event if a very urgent deadline is found.
    """
    print(f"Background processing email: '{email_subject}' from '{email_sender}'")
    try:
        analysis = analyze_email_sentiment(email_text)
        
        print(f"  Sentiment: {analysis.sentiment} (Score: {analysis.sentiment_score:.2f})")
        print(f"  Urgency (ML): {analysis.urgency_level} (Score: {analysis.ml_urgency_score})")
        print(f"  Deadline: {analysis.deadline}")

        if analysis.ml_urgency_score == 2 and analysis.deadline: # Very Urgent
            print(f"  -> Detected VERY URGENT email with deadline: '{analysis.deadline}'. Creating calendar event...")
            start_dt, end_dt = parse_deadline_string(analysis.deadline)
            
            if start_dt and end_dt:
                print(f"  Parsed deadline: Start={start_dt.isoformat()}, End={end_dt.isoformat()}")
                event_summary = f"[PARTISH] Deadline: {email_subject}"
                event_description = (f"Email from: {email_sender}\n"
                                     f"Subject: {email_subject}\n"
                                     f"Deadline string: {analysis.deadline}\n"
                                     f"Body preview: {email_text[:200]}...")

                calendar_service = get_calendar_service(calendar_credentials) # Use calendar credentials
                created_event = create_calendar_event(
                    calendar_service,
                    summary=event_summary,
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    description=event_description
                )
                if created_event:
                    print(f"  Successfully created calendar event: {created_event.get('htmlLink')}")
                else:
                    print("  Failed to create calendar event.")
            else:
                print(f"  Could not parse deadline '{analysis.deadline}' into valid dates. Skipping calendar event.")
        elif analysis.ml_urgency_score == 1 and analysis.deadline: # Urgent
            print(f"  -> Detected URGENT email with deadline: '{analysis.deadline}'. Consider creating calendar event...")
            start_dt, end_dt = parse_deadline_string(analysis.deadline)
            if start_dt and end_dt:
                print(f"  Parsed deadline: Start={start_dt.isoformat()}, End={end_dt.isoformat()}")
            else:
                print(f"  Could not parse deadline '{analysis.deadline}' into valid dates.")
        else:
            print("  -> No urgent deadline detected or email not Very Urgent. Skipping calendar event creation.")
    except Exception as e:
        print(f"Error processing email in background: {e}")

@router.post("/process_inbox")
async def process_user_inbox(
    background_tasks: BackgroundTasks,
    gmail_credentials: Credentials = Depends(get_google_credentials),
    calendar_credentials: Credentials = Depends(get_google_credentials) # Re-added
):
    """
    Fetches recent emails, analyzes them for urgency and deadlines,
    and automatically processes them (calendar event creation is currently disabled).
    Runs in the background to avoid blocking the API response.
    """
    print("Initiating background inbox processing...")
    try:
        gmail_service = get_gmail_service(gmail_credentials)
        
        results = gmail_service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages:
            return {"message": "No new messages found to process."}

        for msg_obj in messages:
            msg_id = msg_obj['id']
            sender, subject, body = get_email_details(gmail_service, msg_id)
            full_email_text = f"{subject} {body}"
            
            # Offload heavy processing to a background task
            background_tasks.add_task(
                _process_email_background,
                full_email_text,
                subject,
                sender,
                gmail_credentials, # Pass credentials explicitly
                calendar_credentials # Pass credentials explicitly
            )
        
        return {"message": f"Processing of {len(messages)} messages initiated in background."}

    except HttpError as error:
        raise HTTPException(status_code=error.resp.status, detail=f"Gmail API error: {error.content.decode()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

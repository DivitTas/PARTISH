from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from app.routers.auth import get_google_credentials
from src.calendar_api import get_calendar_service, create_calendar_event
from src.date_parser import parse_deadline_string

router = APIRouter()

@router.post("/events")
async def create_calendar_event_endpoint(
    summary: str = Body(..., embed=True),
    deadline_str: str = Body(..., embed=True),
    description: str = Body("", embed=True),
    calendar_id: str = Body("primary", embed=True),
    time_zone: str = Body("America/New_York", embed=True),
    credentials: Credentials = Depends(get_google_credentials)
):
    """
    Creates a Google Calendar event from a natural language deadline string.
    """
    try:
        start_dt, end_dt = parse_deadline_string(deadline_str)

        if not start_dt or not end_dt:
            raise HTTPException(status_code=400, detail=f"Could not parse deadline string: '{deadline_str}'")

        calendar_service = get_calendar_service(credentials)
        
        event = create_calendar_event(
            calendar_service,
            summary=summary,
            start_datetime=start_dt,
            end_datetime=end_dt,
            description=description,
            calendar_id=calendar_id,
            time_zone=time_zone
        )
        if event:
            return {"message": "Calendar event created successfully!", "event_link": event.get('htmlLink')}
        else:
            raise HTTPException(status_code=500, detail="Failed to create calendar event.")

    except HttpError as error:
        raise HTTPException(status_code=error.resp.status, detail=f"Calendar API error: {error.content.decode()}")
    except ValueError as e: # From get_calendar_service for invalid credentials
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

import os
import pickle
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# If modifying these scopes, delete the file token.pickle.
# 'offline_access' is important for long-lived access tokens
SCOPES = ['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly']
# Alternatively, for full calendar access: ['https://www.googleapis.com/auth/calendar']

TOKEN_PICKLE_CALENDAR = 'token_calendar.pickle'
# CLIENT_SECRETS_FILE is no longer used directly for client ID/Secret.
# These should be set as environment variables.
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CALENDAR_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET')

def get_calendar_service():
    """Shows basic usage of the Google Calendar API.
    """
    creds = None
    if os.path.exists(TOKEN_PICKLE_CALENDAR):
        with open(TOKEN_PICKLE_CALENDAR, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
                print("Error: GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET environment variables must be set.")
                print("Alternatively, ensure a client_secret.json file is available if using that method (commented out).")
                return None

            # Create an InstalledAppFlow with client ID and secret from env vars
            flow = InstalledAppFlow.from_client_config(
                client_config={
                    "web": { # Or "installed" depending on your client type
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                    }
                },
                scopes=SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE_CALENDAR, 'wb') as token:
            pickle.dump(creds, token)

    if creds:
        service = build('calendar', 'v3', credentials=creds)
        return service
    return None

def create_calendar_event(
    service,
    summary: str,
    start_datetime: datetime,
    end_datetime: datetime,
    description: str = '',
    calendar_id: str = 'primary',
    time_zone: str = 'America/New_York' # Default timezone
):
    """
    Creates a Google Calendar event.

    Args:
        service: Google Calendar API service object.
        summary: Title of the event.
        start_datetime: Start time of the event (datetime object).
        end_datetime: End time of the event (datetime object).
        description: Description of the event.
        calendar_id: The ID of the calendar to create the event on (e.g., 'primary').
        time_zone: The timezone for the event.
    """
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': time_zone,
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': time_zone,
        },
    }

    try:
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
        return event
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

# --- Example Usage ---
if __name__ == "__main__":
    print("Script started: Initializing Google Calendar API setup.")
    try:
        calendar_service = get_calendar_service()
        print("Google Calendar service initialized successfully.")

        # Example: Create an event for tomorrow's deadline
        # Replace with parsed datetime from email analysis
        tomorrow = datetime.now() + timedelta(days=1)
        event_start = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        event_end = tomorrow.replace(hour=17, minute=0, second=0, microsecond=0)

        print("\nAttempting to create a test event...")
        test_event = create_calendar_event(
            calendar_service,
            summary="Test Deadline from PARTISH",
            start_datetime=event_start,
            end_datetime=event_end,
            description="This is a test event created by PARTISH for a deadline."
        )
        if test_event:
            print("Test event created successfully!")
        else:
            print("Failed to create test event.")

    except Exception as e:
        print(f"An error occurred during Calendar API setup or event creation: {e}")
        print("Please ensure your 'client_secret.json' is correctly configured and the Calendar API is enabled.")
    print("\nScript finished.")

import os
from datetime import datetime
from src.gmail_access import authenticate_gmail, get_email_details
from src.JSON_Extracter import analyze_email_sentiment
from src.date_parser import parse_deadline_string
from src.calendar_api import get_calendar_service, create_calendar_event

def main():
    print("Starting PARTISH main processor...")

    # --- 1. Authenticate with Gmail ---
    print("Authenticating with Gmail...")
    gmail_service = authenticate_gmail()
    if not gmail_service:
        print("Failed to authenticate with Gmail. Exiting.")
        return

    # --- 2. Authenticate with Google Calendar ---
    print("Authenticating with Google Calendar...")
    calendar_service = get_calendar_service()
    if not calendar_service:
        print("Failed to authenticate with Google Calendar. Exiting.")
        return

    # --- 3. Fetch Emails (e.g., last 5 unread) ---
    print("Fetching recent emails from Gmail...")
    try:
        # Fetch up to 5 unread messages. Adjust query as needed.
        # 'q': 'is:unread' could be added to fetch only unread.
        results = gmail_service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages:
            print("No new messages found.")
            return

        print(f"Found {len(messages)} recent messages.")

        for msg_obj in messages:
            msg_id = msg_obj['id']
            sender, subject, body = get_email_details(gmail_service, msg_id)
            full_email_text = f"{subject} {body}"

            print(f"
--- Analyzing Email: '{subject}' from '{sender}' ---")
            analysis = analyze_email_sentiment(full_email_text)
            
            print(f"  Sentiment: {analysis.sentiment} (Score: {analysis.sentiment_score:.2f})")
            print(f"  Urgency (ML): {analysis.urgency_level} (Score: {analysis.ml_urgency_score})")
            print(f"  Deadline: {analysis.deadline}")

            # --- 4. Process Urgent Emails with Deadlines ---
            if analysis.ml_urgency_score == 2 and analysis.deadline: # Very Urgent
                print(f"  -> Detected VERY URGENT email with deadline: '{analysis.deadline}'. Creating calendar event...")
                start_dt, end_dt = parse_deadline_string(analysis.deadline)
                
                if start_dt and end_dt:
                    event_summary = f"[PARTISH] Deadline: {subject}"
                    event_description = f"Email from: {sender}
Subject: {subject}
Body preview: {body[:200]}..."

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
                # You might want to ask the user for confirmation here, or just create it.
                # For now, we'll just log it.
                start_dt, end_dt = parse_deadline_string(analysis.deadline)
                if start_dt and end_dt:
                    print(f"  Parsed deadline: Start={start_dt.isoformat()}, End={end_dt.isoformat()}")
                else:
                    print(f"  Could not parse deadline '{analysis.deadline}' into valid dates.")
            else:
                print("  -> No urgent deadline detected or email not Very Urgent. Skipping calendar event creation.")

    except Exception as e:
        print(f"An unexpected error occurred in main processor: {e}")

    print("
PARTISH main processor finished.")

if __name__ == "__main__":
    main()

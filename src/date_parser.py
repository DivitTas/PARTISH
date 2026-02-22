from datetime import datetime, time, timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from typing import Tuple, Optional
import re

def _parse_common_relative_date(text: str, base_date: datetime) -> Optional[datetime.date]:
    """Helper to parse common relative date terms."""
    text_lower = text.lower()
    base_date_no_time = base_date.replace(hour=0, minute=0, second=0, microsecond=0)

    if "tomorrow" in text_lower:
        return (base_date_no_time + timedelta(days=1)).date()
    elif "today" in text_lower:
        return base_date_no_time.date()
    elif "next week" in text_lower:
        return (base_date_no_time + relativedelta(weeks=+1)).date()
    elif "next month" in text_lower:
        return (base_date_no_time + relativedelta(months=+1)).date()
    elif "end of week" in text_lower or "eow" in text_lower:
        # Default EOW to Friday. If today is already Friday, then next Friday.
        # Weekday(FR) means the next Friday
        return (base_date_no_time + relativedelta(weekday=FR)).date()
    elif "end of day" in text_lower or "eod" in text_lower: # If EOD is specific without a date, use today
        return base_date_no_time.date()

    return None

def parse_deadline_string(deadline_str: str, base_date: datetime = None) -> Tuple[datetime, datetime]:
    """
    Parses a natural language deadline string into start and end datetime objects for a calendar event.

    Args:
        deadline_str: The string extracted as a deadline (e.g., "by Friday", "22 October 2025", "EOD tomorrow").
        base_date: The reference date for relative deadlines (e.g., 'today', 'tomorrow'). Defaults to now.

    Returns:
        A tuple of (start_datetime, end_datetime) for the event.
        Returns (None, None) if the string cannot be reliably parsed into a date.
    """
    if base_date is None:
        base_date = datetime.now()
    
    # Define default times for events without explicit time
    default_start_time = time(9, 0, 0) # 9 AM
    default_end_time = time(17, 0, 0)  # 5 PM (for full-day events)
    eod_override_time = time(17, 0, 0) # 5 PM for explicit EOD

    # Prepare a default datetime object for parse() call
    # This provides a base date and default time for missing components
    default_dt_for_parse_call = base_date.replace(
        hour=default_start_time.hour,
        minute=default_start_time.minute,
        second=0, microsecond=0
    )

    deadline_lower = deadline_str.lower()
    
    try:
        # --- 1. Determine the Date Component ---
        parsed_date_component = None
        
        # First, try explicit relative date keywords
        parsed_date_component = _parse_common_relative_date(deadline_str, base_date)
        
        # If not found by helper, use dateutil.parser for the date part
        temp_parsed_dt = None
        if parsed_date_component is None:
            try:
                temp_parsed_dt = parse(deadline_str,
                                       default=default_dt_for_parse_call,
                                       fuzzy=True,
                                       ignoretz=True)
                parsed_date_component = temp_parsed_dt.date()
            except ValueError: # dateutil couldn't find a date
                parsed_date_component = None

        if parsed_date_component is None:
            return None, None # Still no date found

        # --- 2. Determine the Time Component ---
        parsed_time_component = None
        # Try to extract time specifically if dateutil already parsed it
        if temp_parsed_dt and temp_parsed_dt.time() != default_dt_for_parse_call.time():
            parsed_time_component = temp_parsed_dt.time()
        else: # Try to parse time from string after date part is "removed"
            # Attempt to strip date info from string to isolate time
            time_str_candidate = re.sub(r'\b(?:' + '|'.join([
                'january', 'february', 'march', 'april', 'may', 'june',
                'july', 'august', 'september', 'october', 'november', 'december',
                'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
                'today', 'tomorrow', 'next week', 'next month', 'eod', 'eow',
                r'\d{1,2}(?:st|nd|rd|th)?', # day of month
                r'\d{4}', # year
            ]) + r')\b', '', deadline_lower, flags=re.IGNORECASE).strip()
            
            # Now try to parse time from the cleaned string
            try:
                time_only_dt = parse(time_str_candidate, fuzzy=True, default=default_dt_for_parse_call)
                if time_only_dt.time() != default_dt_for_parse_call.time():
                    parsed_time_component = time_only_dt.time()
            except ValueError:
                pass


        # --- 3. Construct start_dt and end_dt ---
        start_dt = datetime.combine(parsed_date_component, parsed_time_component if parsed_time_component else default_start_time)
        
        # Adjust for 'EOD' override
        if "eod" in deadline_lower or "end of day" in deadline_lower:
            start_dt = start_dt.replace(hour=eod_override_time.hour, minute=eod_override_time.minute)
            end_dt = start_dt + timedelta(hours=1) # EOD is typically a point, assume 1hr event
        elif parsed_time_component: # If a specific time was parsed
            end_dt = start_dt + timedelta(hours=1) # Assume 1 hour event
        else: # No specific time, use default workday
            end_dt = start_dt.replace(hour=default_end_time.hour, minute=default_end_time.minute)

        # --- 4. Heuristic: Ensure future-oriented dates are in the future ---
        # If the parsed date (ignoring time) is before the base date, and it's a relative term (e.g. "Friday")
        # that should mean an upcoming date, advance it by a week.
        if start_dt.date() < base_date.date():
            # Avoid advancing explicit dates like "22 October 2025" if they are in the past (missed deadline).
            # This is a bit tricky, but we can check if the original string explicitly contains a year.
            has_explicit_year = bool(re.search(r'\d{4}', deadline_str))
            
            if not has_explicit_year: # If no explicit year, it's likely a relative term that needs advancing
                start_dt += relativedelta(weeks=+1)
                end_dt += relativedelta(weeks=+1)

        return start_dt, end_dt

    except Exception as e:
        print(f"Could not parse deadline string '{deadline_str}': {e}")
        return None, None

# --- Example Usage (for testing the parser) ---
if __name__ == "__main__":
    print("Script started.")
    print("--- Date Parser Test ---")
    print(f"Base Date: {datetime.now()}\n")

    test_deadlines = [
        "by Friday",
        "22 October 2025",
        "EOD tomorrow",
        "next Tuesday 3 PM",
        "due 2 days from now",
        "next week",
        "next month",
        "tomorrow",
        "6pm (UK time) on 22 October 2025" # From Cambridge email
    ]

    for dl_str in test_deadlines:
        print(f"Testing: '{dl_str}'")
        start_dt, end_dt = parse_deadline_string(dl_str)
        if start_dt and end_dt:
            print(f"  -> Start: {start_dt.isoformat()}, End: {end_dt.isoformat()}")
        else:
            print(f"  -> Could not parse.")
        print("-" * 30)
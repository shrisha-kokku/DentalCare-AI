from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN


def _get_calendar_service():
    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )
    return build("calendar", "v3", credentials=creds)


def create_calendar_event(date_slot: str, doctor_name: str, patient_id: str) -> str | None:
    """Creates a calendar event with a reminder. Returns the event ID, or None if it fails."""
    start = datetime.strptime(date_slot, "%m/%d/%Y %H:%M")
    end = start + timedelta(minutes=30)
    event_body = {
        "summary": f"Dental appointment with Dr. {doctor_name.title()}",
        "description": f"Patient ID: {patient_id}",
        "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Kolkata"},
        "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 60}]},
    }
    try:
        created = _get_calendar_service().events().insert(calendarId="primary", body=event_body).execute()
        return created.get("id")
    except Exception:
        return None


def delete_calendar_event(event_id: str) -> bool:
    """Deletes a calendar event by ID. Returns True on success, False if it fails or there's no ID."""
    if not event_id:
        return False
    try:
        _get_calendar_service().events().delete(calendarId="primary", eventId=event_id).execute()
        return True
    except Exception:
        return False
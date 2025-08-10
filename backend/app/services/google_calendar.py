import os, datetime
from typing import Tuple, List, Dict, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def build_creds(refresh_token: str, client_id: str, client_secret: str) -> Credentials:
    return Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=GOOGLE_SCOPES,
    )

def list_events(refresh_token: str, start_iso: str, end_iso: str) -> List[Dict]:
    creds = build_creds(refresh_token, os.getenv("GOOGLE_CLIENT_ID"), os.getenv("GOOGLE_CLIENT_SECRET"))
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_iso,
        timeMax=end_iso,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    return events_result.get("items", [])

def upsert_event(refresh_token: str, summary: str, start_iso: str, end_iso: str, event_id: Optional[str] = None) -> Dict:
    creds = build_creds(refresh_token, os.getenv("GOOGLE_CLIENT_ID"), os.getenv("GOOGLE_CLIENT_SECRET"))
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    body = {
        "summary": summary,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
    }
    if event_id:
        return service.events().patch(calendarId="primary", eventId=event_id, body=body).execute()
    return service.events().insert(calendarId="primary", body=body).execute()

def list_busy_for_day(refresh_token: str, day_utc: datetime) -> list[dict]:
    start_iso = day_utc.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end_iso = (day_utc.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()
    items = list_events(refresh_token, start_iso, end_iso)
    out = []
    for e in items:
        start = e.get("start",{}).get("dateTime")
        end = e.get("end",{}).get("dateTime")
        if start and end:
            out.append({"id": e.get("id"), "start": start, "end": end, "summary": e.get("summary")})
    return out 
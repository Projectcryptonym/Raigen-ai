from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.repo import integrations_ref
from ..services.google_calendar import list_events, upsert_event
from datetime import datetime, timedelta, timezone

router = APIRouter()

def iso(dt):
    return dt.replace(microsecond=0).astimezone(timezone.utc).isoformat()

@router.get("/sync")
async def sync_calendar(user_id: str, days: int = Query(14, ge=1, le=30)):
    doc = integrations_ref().document(user_id).get()
    if not doc.exists:
        raise HTTPException(400, "No Google integration for user")
    refresh_token = doc.to_dict().get("google", {}).get("refresh_token")
    if not refresh_token:
        raise HTTPException(400, "Missing refresh_token")

    start = datetime.now(timezone.utc)
    end = start + timedelta(days=days)
    items = list_events(refresh_token, iso(start), iso(end))
    events = [{
        "id": e.get("id"),
        "summary": e.get("summary"),
        "start": e.get("start", {}).get("dateTime"),
        "end": e.get("end", {}).get("dateTime")
    } for e in items]
    return {"events": events}

class BlockIn(BaseModel):
    user_id: str
    title: str
    start_iso: str
    end_iso: str
    event_id: Optional[str] = None

@router.post("/block")
async def create_or_update_block(body: BlockIn):
    doc = integrations_ref().document(body.user_id).get()
    if not doc.exists:
        raise HTTPException(400, "No Google integration for user")
    refresh_token = doc.to_dict().get("google", {}).get("refresh_token")
    if not refresh_token:
        raise HTTPException(400, "Missing refresh_token")

    event = upsert_event(refresh_token, body.title, body.start_iso, body.end_iso, body.event_id)
    return {"event_id": event.get("id"), "summary": event.get("summary")} 
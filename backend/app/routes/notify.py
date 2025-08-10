from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from ..services.repo import set_doc, get_doc

router = APIRouter()

class PushTokenIn(BaseModel):
    user_id: str
    expo_push_token: str

@router.post("/register")
def register_token(body: PushTokenIn):
    set_doc("users", body.user_id, {"expo_push_token": body.expo_push_token})
    return {"ok": True}

class PushIn(BaseModel):
    user_id: str
    title: str
    body: str

@router.post("/expo")
async def send_expo(body: PushIn):
    doc = get_doc("users", body.user_id)
    if not doc.exists:
        raise HTTPException(404, "user not found")
    token = doc.to_dict().get("expo_push_token")
    if not token:
        raise HTTPException(400, "user has no expo_push_token")

    payload = {"to": token, "title": body.title, "body": body.body}
    async with httpx.AsyncClient() as client:
        r = await client.post("https://exp.host/--/api/v2/push/send", json=payload, timeout=20)
        r.raise_for_status()
        return {"sent": True, "expo": r.json()} 
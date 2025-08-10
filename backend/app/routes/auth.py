import os, urllib.parse, json, base64
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from ..services.repo import integrations_ref, set_doc

router = APIRouter()

class OAuthStartResponse(BaseModel):
    auth_url: str

@router.get("/google/url", response_model=OAuthStartResponse)
def google_oauth_url():
    params = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "scope": "https://www.googleapis.com/auth/calendar.events",
    }
    return {"auth_url": "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)}

@router.post("/google/callback")
async def google_callback(request: Request):
    data = await request.json()
    code = data.get("code")
    user_id = data.get("user_id")  # pass from client after login
    if not code or not user_id:
        raise HTTPException(status_code=400, detail="code and user_id required")

    # exchange code for tokens
    import httpx
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(token_url, data=payload, timeout=20)
        r.raise_for_status()
        tokens = r.json()

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="No refresh_token returned; ensure prompt=consent & access_type=offline")

    integrations_ref().document(user_id).set({
        "google": {
            "refresh_token": refresh_token,
            "scopes": ["calendar.events"]
        }
    }, merge=True)

    return {"ok": True} 
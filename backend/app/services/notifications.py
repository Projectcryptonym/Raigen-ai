import httpx
from ..services.repo import get_doc

async def send_expo_push(user_id: str, title: str, body: str) -> bool:
    doc = get_doc("users", user_id)
    if not doc.exists:
        return False
    token = doc.to_dict().get("expo_push_token")
    if not token:
        return False
    payload = {"to": token, "title": title, "body": body}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post("https://exp.host/--/api/v2/push/send", json=payload, timeout=20)
            r.raise_for_status()
        return True
    except Exception as e:
        print("[notify] expo push failed:", e)
        return False

async def plan_generated(user_id: str, blocks_count: int):
    title = "Your plan is ready"
    body = f"Raigen scheduled {blocks_count} block(s) for today. Open the app to review."
    ok = await send_expo_push(user_id, title, body)
    if not ok:
        print(f"[notify] no push token for {user_id} or send failed") 
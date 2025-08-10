from fastapi import APIRouter
from datetime import datetime, timedelta, timezone
from ..services.memos import memory_store

router = APIRouter()

@router.post("/weekly/generate")
async def weekly_generate(user_id: str):
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=7)
    # MVP: stub data, real version will read plans/messages and compute adherence
    summary = f"Weekly review {start.isoformat()} → {today.isoformat()}: focus on 2 big rocks; lighten Tue/Thu load."
    mem_id = memory_store(kind="review", text=summary, meta={"from": start.isoformat(), "to": today.isoformat(), "user_id": user_id})
    return {"summary": summary, "mem_id": mem_id} 
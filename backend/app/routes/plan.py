from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from ..services.memos import memory_store
from ..services.repo import save_plan, get_plan, integrations_ref
from ..services.budgets import get_current, atomic_inc, within_limit
from ..services.notifications import plan_generated
from ..services.free_windows import build_free_windows
from ..services.google_calendar import list_events, upsert_event
from ..services.llm import plan_rationale
from ..services.tasks import propose_tasks_from_goals

router = APIRouter()

class GenerateIn(BaseModel):
    user_id: str
    tasks: list  # list of {"title","goal_id","effort_min","energy","urgency","impact"}
    free_windows: list  # list of {"start_iso","end_iso"} in UTC
    user_prefs: dict    # quiet_hours, hard_blocks, max_day_min

@router.get("/today")
async def get_today_plan(user_id: str):
    today = datetime.now(timezone.utc).date().isoformat()
    doc = get_plan(user_id, today)
    if not doc.exists:
        return {"date": today, "blocks": []}
    return doc.to_dict()

@router.post("/generate")
async def generate_plan(body: GenerateIn):
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Check plan limits (1 full + 2 replans/day)
    existing = get_plan(body.user_id, today)
    is_replan = existing.exists and bool(existing.to_dict().get("blocks"))
    if is_replan:
        data = existing.to_dict()
        replan_count = int(data.get("replan_count", 0))
        if replan_count >= 2:
            raise HTTPException(status_code=429, detail="Replan limit reached for today")
    
    # Get user's Google refresh token
    doc = integrations_ref().document(body.user_id).get()
    refresh_token = doc.to_dict().get("google", {}).get("refresh_token") if doc.exists else None
    
    # Auto-propose tasks from goals if none provided
    tasks = body.tasks
    if not tasks:
        tasks = propose_tasks_from_goals(body.user_id)
    
    # Convert windows or auto-discover if empty
    windows = []
    if not body.free_windows and refresh_token:
        # Auto-discover free windows from Google Calendar
        today0 = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        items = list_events(refresh_token, today0.isoformat(), (today0 + timedelta(days=1)).isoformat())
        busy = [{"start": i.get("start",{}).get("dateTime"), "end": i.get("end",{}).get("dateTime")} for i in items if i.get("start") and i.get("end")]
        free = build_free_windows(today0, today0 + timedelta(days=1), busy)
        windows = free
    else:
        # Use provided windows
        for w in body.free_windows:
            s = datetime.fromisoformat(w["start_iso"].replace("Z","+00:00"))
            e = datetime.fromisoformat(w["end_iso"].replace("Z","+00:00"))
            windows.append((s, e))
    
    # Existing blocks today (MVP: none; you can pass if needed)
    existing_blocks = []
    blocks = pack_tasks(windows, tasks, body.user_prefs, existing_blocks)
    
    # Add goal_id to blocks when present
    for i, block in enumerate(blocks):
        if i < len(tasks) and tasks[i].get("goal_id"):
            block["goal_id"] = tasks[i]["goal_id"]
    
    # Create Google events for each block if we have a refresh token
    if refresh_token:
        for b in blocks:
            upsert_event(refresh_token, b["title"], b["start"], b["end"])
    
    # Generate rationale
    rationale = plan_rationale(tasks, body.user_prefs, blocks)
    
    # Estimate LLM cost (stub): 5 cents for rationale; adjust when wired
    LLM_EST_CENTS = 5
    # Enforce monthly LLM cap softly (skip if not within limit)
    if not within_limit(body.user_id, "llm_cents", LLM_EST_CENTS, "llm_limit_cents"):
        # Still save plan but log; you could early return or degrade here
        print("[budgets] LLM soft cap exceeded for", body.user_id)
    
    # Save plan with plan type and replan count
    payload = {"user_id": body.user_id, "date": today, "blocks": blocks, "rationale": rationale}
    if is_replan:
        payload["replan_count"] = replan_count + 1
        payload["plan_type"] = "replan"
    else:
        payload["replan_count"] = 0
        payload["plan_type"] = "full"
    save_plan(body.user_id, today, blocks, rationale)
    
    # Increment budgets
    atomic_inc(body.user_id, {"llm_cents": LLM_EST_CENTS})
    
    # Store memory
    memory_store(kind="plan", text=rationale, meta={"date": today, "blocks": len(blocks)})
    
    # Notify user
    await plan_generated(body.user_id, len(blocks))
    
    return {"date": today, "blocks": blocks, "rationale": rationale, "plan_type": payload["plan_type"], "replan_count": payload["replan_count"]}

class ReplanIn(BaseModel):
    user_id: str
    delta_minutes: int = 30

@router.post("/replan")
async def replan(body: ReplanIn):
    today = datetime.now(timezone.utc).date().isoformat()
    memory_store(kind="plan", text="Delta replan requested", meta={"date": today, "delta": body.delta_minutes})
    return {"ok": True}

class CompleteIn(BaseModel):
    user_id: str
    block_id: str
    completed: bool = True

@router.post("/complete")
async def mark_complete(body: CompleteIn):
    today = datetime.now(timezone.utc).date().isoformat()
    doc = get_plan(body.user_id, today)
    if not doc.exists:
        raise HTTPException(404, "No plan for today")
    data = doc.to_dict()
    blocks = data.get("blocks", [])
    found = False
    for b in blocks:
        if b.get("id") == body.block_id or b.get("title") == body.block_id:
            b["completed"] = body.completed
            found = True
            break
    if not found:
        raise HTTPException(404, "Block not found")
    # simple adherence count
    completed = sum(1 for b in blocks if b.get("completed"))
    data["adherence"] = {"completed": completed, "planned": len(blocks)}
    # save back
    from ..services.repo import set_doc
    set_doc("plans", f"{body.user_id}@{today}", data)
    return {"ok": True, "adherence": data["adherence"]} 
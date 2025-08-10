from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple
import hashlib
import json
from .conflict_engine import within_quiet_hours, hard_block_conflict, exceeds_daily_load

def _block_id(b: Dict) -> str:
    """Generate stable block ID based on content"""
    seed = json.dumps([b["title"], b["start"], b["end"], b.get("goal_id")], sort_keys=True)
    return hashlib.sha1(seed.encode()).hexdigest()[:10]

def score(task: Dict) -> float:
    urgency = float(task.get("urgency", 1.0))
    impact = float(task.get("impact", 1.0))
    effort = max(int(task.get("effort_min", 30)), 15)
    return (urgency * impact) / effort

def pack_tasks(free_windows: List[Tuple[datetime, datetime]],
               tasks: List[Dict],
               user_prefs: Dict,
               existing_blocks_today: List[Dict]) -> List[Dict]:
    """
    free_windows: list of (start_dt, end_dt) UTC
    tasks: [{"title","goal_id","effort_min","energy","urgency","impact"}]
    user_prefs: {"quiet_hours":{"start":"22:00","end":"07:00"},"hard_blocks":[...],"max_day_min": 300}
    returns plan blocks [{"title","start","end","goal_id","energy","locked":False}]
    """
    q = user_prefs.get("quiet_hours", {"start":"22:00","end":"07:00"})
    quiet_s = _parse_time(q["start"]); quiet_e = _parse_time(q["end"])
    hard_blocks = user_prefs.get("hard_blocks", [])
    max_day = int(user_prefs.get("max_day_min", 300))

    out: List[Dict] = []
    for t in sorted(tasks, key=score, reverse=True):
        placed = False
        need = int(t.get("effort_min", 30))
        for (ws, we) in free_windows:
            # attempt top-anchored placement, single block MVP
            cand_s = ws
            while cand_s + timedelta(minutes=need) <= we:
                cand_e = cand_s + timedelta(minutes=need)
                # checks
                if within_quiet_hours(cand_s, cand_e, quiet_s, quiet_e):
                    cand_s = cand_s + timedelta(minutes=15); continue
                # MVP: hard block conflict check by local time -> assume user TZ later; use UTC now
                if hard_block_conflict(cand_s, cand_e, hard_blocks):
                    cand_s = cand_s + timedelta(minutes=15); continue
                if exceeds_daily_load(existing_blocks_today + _as_blocks(out), need, max_minutes_per_day=max_day):
                    # cannot place more today
                    break
                blk = {
                    "title": t["title"],
                    "start": _iso(cand_s),
                    "end": _iso(cand_e),
                    "goal_id": t.get("goal_id"),
                    "energy": t.get("energy", None),
                    "locked": False
                }
                blk["id"] = _block_id(blk)
                out.append(blk)
                placed = True
                break
            if placed: break
    return out

def _as_blocks(plan_blocks: List[Dict]) -> List[Dict]:
    return [{"start": b["start"], "end": b["end"]} for b in plan_blocks]

def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0, tzinfo=timezone.utc).isoformat().replace("+00:00","Z")

def _parse_time(hhmm: str):
    from datetime import time
    return time.fromisoformat(hhmm) 
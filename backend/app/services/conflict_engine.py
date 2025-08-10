from datetime import datetime, time, timedelta
from typing import List, Dict

def within_quiet_hours(dt_start: datetime, dt_end: datetime, quiet_start: time, quiet_end: time) -> bool:
    # Handles windows that cross midnight
    def in_q(dt):
        t = dt.time()
        if quiet_start <= quiet_end:
            return quiet_start <= t < quiet_end
        # crosses midnight
        return t >= quiet_start or t < quiet_end
    return in_q(dt_start) or in_q(dt_end - timedelta(seconds=1))

def hard_block_conflict(dt_start: datetime, dt_end: datetime, hard_blocks: List[Dict]) -> bool:
    # hard_blocks: [{"label":"work","start":"09:00","end":"17:00","days":[1,2,3,4,5]}]
    wd = dt_start.isoweekday()
    for hb in hard_blocks:
        if wd not in hb.get("days", []): 
            continue
        s = time.fromisoformat(hb["start"])
        e = time.fromisoformat(hb["end"])
        # same-day comparison only (MVP)
        if not (dt_end.time() <= s or dt_start.time() >= e):
            return True
    return False

def exceeds_daily_load(existing_blocks: List[Dict], candidate_min: int, max_minutes_per_day: int = 300) -> bool:
    # existing_blocks items: {"start": iso, "end": iso}
    total = 0
    for b in existing_blocks:
        # naive compute; assume same day
        total += _duration_min(b["start"], b["end"])
    return (total + candidate_min) > max_minutes_per_day

def _duration_min(start_iso: str, end_iso: str) -> int:
    from datetime import datetime, timezone
    s = datetime.fromisoformat(start_iso.replace("Z","+00:00"))
    e = datetime.fromisoformat(end_iso.replace("Z","+00:00"))
    return int((e - s).total_seconds() // 60) 
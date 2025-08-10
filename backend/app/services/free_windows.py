from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Dict

def build_free_windows(day_start: datetime, day_end: datetime, busy_events: List[Dict]) -> List[Tuple[datetime, datetime]]:
    # busy_events: [{"start":"...","end":"..."}] ISO 8601
    busy = []
    for e in busy_events:
        s = datetime.fromisoformat(e["start"].replace("Z","+00:00"))
        e_ = datetime.fromisoformat(e["end"].replace("Z","+00:00"))
        # clamp within the day
        s = max(s, day_start); e_ = min(e_, day_end)
        if e_ > s: busy.append((s, e_))
    busy.sort(key=lambda x: x[0])

    free = []
    cur = day_start
    for (bs, be) in busy:
        if bs > cur:
            free.append((cur, bs))
        cur = max(cur, be)
    if cur < day_end:
        free.append((cur, day_end))
    # remove tiny gaps < 15min
    free = [(s,e) for (s,e) in free if (e - s) >= timedelta(minutes=15)]
    return free 
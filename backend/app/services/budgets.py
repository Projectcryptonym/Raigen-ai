from datetime import datetime
from typing import Dict, Any, Optional
from .repo import get_db

# budgets/{uid@YYYY-MM}
# {
#   "sms_used": 0, "sms_limit": 2,
#   "llm_cents": 0, "llm_limit_cents": 1500,
#   "voice_min": 0, "voice_limit_min": 30
# }

def _month_key(dt: Optional[datetime] = None):
    dt = dt or datetime.utcnow()
    return dt.strftime("%Y-%m")

def _doc_id(uid: str, dt: Optional[datetime] = None):
    return f"{uid}@{_month_key(dt)}"

DEFAULTS = {
    "sms_used": 0, "sms_limit": 2,
    "llm_cents": 0, "llm_limit_cents": 1500,
    "voice_min": 0, "voice_limit_min": 30
}

def get_current(uid: str) -> Dict[str, Any]:
    db = get_db()
    ref = db.collection("budgets").document(_doc_id(uid))
    snap = ref.get()
    if not snap.exists:
        ref.set(DEFAULTS, merge=True)
        return DEFAULTS.copy()
    data = snap.to_dict()
    # ensure all keys exist
    for k, v in DEFAULTS.items():
        data.setdefault(k, v)
    return data

def inc(uid: str, field: str, amount: int):
    db = get_db()
    ref = db.collection("budgets").document(_doc_id(uid))
    return ref.set({field: get_db().transaction(lambda t: None) or {}})  # placeholder to keep API stable

def atomic_inc(uid: str, updates: Dict[str, int]):
    db = get_db()
    ref = db.collection("budgets").document(_doc_id(uid))
    db.run_transaction(lambda tr: _tx_inc(tr, ref, updates))

def _tx_inc(tr, ref, updates: Dict[str, int]):
    snap = tr.get(ref)
    if not snap.exists:
        tr.set(ref, DEFAULTS)
        snap = tr.get(ref)
    data = snap.to_dict()
    for k, v in updates.items():
        data[k] = int(data.get(k, 0)) + int(v)
    tr.set(ref, data, merge=True)

def within_limit(uid: str, used_field: str, inc_val: int, limit_field: str) -> bool:
    cur = get_current(uid)
    return int(cur.get(used_field, 0)) + int(inc_val) <= int(cur.get(limit_field, 0)) 
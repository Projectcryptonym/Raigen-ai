from .firebase_client import get_db
from typing import Any, Dict, Optional

def users_ref():
    return get_db().collection("users")

def integrations_ref():
    return get_db().collection("integrations")

def plans_ref():
    return get_db().collection("plans")

def budgets_ref():
    return get_db().collection("budgets")

def goals_ref():
    return get_db().collection("goals")

def set_doc(collection: str, doc_id: str, data: Dict[str, Any]):
    return get_db().collection(collection).document(doc_id).set(data, merge=True)

def get_doc(collection: str, doc_id: str):
    return get_db().collection(collection).document(doc_id).get()

from datetime import datetime

def plan_doc_id(user_id: str, date_iso: str) -> str:
    return f"{user_id}@{date_iso}"

def save_plan(user_id: str, date_iso: str, blocks: list, rationale: Optional[str] = None):
    data = {"user_id": user_id, "date": date_iso, "blocks": blocks, "rationale": rationale}
    return set_doc("plans", plan_doc_id(user_id, date_iso), data)

def get_plan(user_id: str, date_iso: str):
    return get_doc("plans", plan_doc_id(user_id, date_iso)) 
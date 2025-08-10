from fastapi import APIRouter
router = APIRouter()

@router.get("/bootstrap")
def bootstrap(user_id: str):
    # MVP: return user prefs & caps; expand later from Firestore
    return {
        "user_id": user_id,
        "prefs": {"quiet_hours":{"start":"22:00","end":"07:00"}, "max_day_min": 300},
        "caps": {"sms_limit": 2, "llm_cents_limit": 1500}
    } 
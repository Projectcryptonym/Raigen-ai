from fastapi import APIRouter, HTTPException
from ..services.budgets import get_current

router = APIRouter()

@router.get("/current")
def budgets_current(user_id: str):
    return get_current(user_id) 
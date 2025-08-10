from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from ..services.repo import set_doc, get_doc, goals_ref
from datetime import datetime

router = APIRouter()

class GoalCreate(BaseModel):
    user_id: str
    title: str
    priority: int
    effort_estimate_min: int
    domain: List[str]
    why: str

class Goal(GoalCreate):
    id: str
    status: str = "active"
    created_at: str
    updated_at: str

@router.post("/")
async def create_goal(goal: GoalCreate):
    """Create a new goal"""
    goal_id = f"{goal.user_id}_{datetime.now().isoformat()}"
    goal_data = {
        "user_id": goal.user_id,
        "title": goal.title,
        "priority": goal.priority,
        "effort_estimate_min": goal.effort_estimate_min,
        "domain": goal.domain,
        "why": goal.why,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    set_doc("goals", goal_id, goal_data)
    return {"id": goal_id, **goal_data}

@router.get("/")
async def list_goals(user_id: str, status: str = "active"):
    """List goals for a user, optionally filtered by status"""
    goals = []
    docs = goals_ref().where("user_id", "==", user_id).where("status", "==", status).stream()
    for doc in docs:
        goals.append({"id": doc.id, **doc.to_dict()})
    return goals 
from typing import List, Dict
from .repo import goals_ref

def propose_tasks_from_goals(user_id: str) -> List[Dict]:
    """
    Propose tasks based on active goals.
    Returns a small set of tasks per active goal (60-120 min tasks).
    """
    # Get active goals
    goals = []
    docs = goals_ref().where("user_id", "==", user_id).where("status", "==", "active").stream()
    for doc in docs:
        goals.append({"id": doc.id, **doc.to_dict()})
    
    if not goals:
        # Return default tasks if no goals
        return [
            {
                "title": "Review and plan day",
                "effort_min": 30,
                "energy": "medium",
                "urgency": 2,
                "impact": 2,
                "goal_id": None
            },
            {
                "title": "Process inbox",
                "effort_min": 45,
                "energy": "low",
                "urgency": 2,
                "impact": 1,
                "goal_id": None
            }
        ]
    
    # Generate tasks from goals
    tasks = []
    for goal in goals:
        # Create 1-2 tasks per goal based on effort estimate
        effort = goal.get("effort_estimate_min", 120)
        priority = goal.get("priority", 2)
        
        # Split large goals into smaller tasks
        if effort > 120:
            # Split into 2 tasks
            task1_effort = effort // 2
            task2_effort = effort - task1_effort
            
            tasks.append({
                "title": f"{goal['title']} - Part 1",
                "effort_min": task1_effort,
                "energy": "high" if priority >= 3 else "medium",
                "urgency": priority,
                "impact": priority,
                "goal_id": goal["id"]
            })
            
            tasks.append({
                "title": f"{goal['title']} - Part 2", 
                "effort_min": task2_effort,
                "energy": "high" if priority >= 3 else "medium",
                "urgency": priority,
                "impact": priority,
                "goal_id": goal["id"]
            })
        else:
            # Single task for smaller goals
            tasks.append({
                "title": goal["title"],
                "effort_min": effort,
                "energy": "high" if priority >= 3 else "medium",
                "urgency": priority,
                "impact": priority,
                "goal_id": goal["id"]
            })
    
    return tasks 
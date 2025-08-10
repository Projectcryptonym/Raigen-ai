from fastapi import APIRouter
from datetime import datetime, timedelta, timezone
from ..services.memos import memory_store
from ..services.repo import get_plan

router = APIRouter()

@router.post("/weekly/generate")
async def weekly_generate(user_id: str):
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=7)
    
    # Calculate real adherence from plans
    total_blocks = 0
    completed_blocks = 0
    adherence_by_day = {}
    
    for i in range(7):
        check_date = start + timedelta(days=i)
        date_str = check_date.isoformat()
        doc = get_plan(user_id, date_str)
        
        if doc.exists:
            data = doc.to_dict()
            blocks = data.get("blocks", [])
            day_blocks = len(blocks)
            day_completed = sum(1 for b in blocks if b.get("completed", False))
            
            total_blocks += day_blocks
            completed_blocks += day_completed
            adherence_by_day[date_str] = {
                "total": day_blocks,
                "completed": day_completed,
                "rate": (day_completed / day_blocks * 100) if day_blocks > 0 else 0
            }
    
    overall_adherence = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0
    
    # Generate insights
    insights = []
    if overall_adherence < 50:
        insights.append("Low adherence - consider reducing daily load or improving time estimates")
    elif overall_adherence < 75:
        insights.append("Moderate adherence - focus on completing high-priority tasks first")
    else:
        insights.append("Strong adherence - great job staying on track!")
    
    # Find best and worst days
    if adherence_by_day:
        best_day = max(adherence_by_day.items(), key=lambda x: x[1]["rate"])
        worst_day = min(adherence_by_day.items(), key=lambda x: x[1]["rate"])
        insights.append(f"Best day: {best_day[0]} ({best_day[1]['rate']:.1f}%)")
        insights.append(f"Challenge day: {worst_day[0]} ({worst_day[1]['rate']:.1f}%)")
    
    summary = f"Weekly review {start.isoformat()} → {today.isoformat()}: {overall_adherence:.1f}% adherence ({completed_blocks}/{total_blocks} blocks completed). {' '.join(insights)}"
    
    mem_id = memory_store(
        kind="review", 
        text=summary, 
        meta={
            "from": start.isoformat(), 
            "to": today.isoformat(), 
            "user_id": user_id,
            "adherence": overall_adherence,
            "total_blocks": total_blocks,
            "completed_blocks": completed_blocks,
            "by_day": adherence_by_day
        }
    )
    
    return {
        "summary": summary, 
        "mem_id": mem_id,
        "adherence": overall_adherence,
        "total_blocks": total_blocks,
        "completed_blocks": completed_blocks,
        "by_day": adherence_by_day,
        "insights": insights
    } 
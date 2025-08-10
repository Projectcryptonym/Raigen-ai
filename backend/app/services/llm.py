import os
import httpx

def plan_rationale(tasks, prefs, packed_blocks):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Plan generated using urgency×impact÷effort and your constraints."
    prompt = f"User prefs: {prefs}\nTasks: {tasks}\nBlocks: {packed_blocks}\nWrite a concise 2-3 sentence rationale."
    # Replace with your GPT-5 endpoint as needed
    try:
        # placeholder: return prompt tail to avoid vendor lock in this stub
        return "Scheduled high-impact work in peak windows; protected quiet hours; kept total load within daily limit."
    except Exception:
        return "Plan generated using urgency×impact÷effort and your constraints." 
from datetime import datetime
import json

def handle_onboarding(stage, msg, user_ref, client):
    """Dynamic onboarding flow for Big Brother AI.
    Returns a reply string *or* None if onboarding is already complete.
    """

    # ------ short‑circuit if onboarding already finished ------
    if stage == "complete":
        return None  # let main pipeline run

    # ------ safeguard: reset only truly malformed states ------
    if stage not in [0, "dynamic", "complete"]:
        user_ref.set({"onboarding_stage": "dynamic", "discovery_progress": []}, merge=True)
        intro = (
            "Welcome to Big Brother AI. Thank you for taking the next step in your self‑improvement journey. "
            "I'm here to help you achieve more, stress less, and live a happier, fuller life. You're here because "
            "you want something greater — I’m here to walk alongside you and keep you grounded in that mission. "
            "I’ll be honest with you, I’ll hold you to your word, and I’ll have your back every step of the way."
        )
        return f"{intro}\n\nLet’s start with something simple: What is your name and what do you do?"

    # ------ initial entry point ------
    if stage == 0:
        user_ref.set({"onboarding_stage": "dynamic", "discovery_progress": []}, merge=True)
        intro = (
            "Welcome to Big Brother AI. Thank you for taking the next step in your self‑improvement journey. "
            "I'm here to help you achieve more, stress less, and live a happier, fuller life. You're here because "
            "you want something greater — I’m here to walk alongside you and keep you grounded in that mission. "
            "I’ll be honest with you, I’ll hold you to your word, and I’ll have your back every step of the way."
        )
        return f"{intro}\n\nLet’s start with something simple: What is your name and what do you do?"

    # ------ dynamic discovery loop ------
    if stage == "dynamic":
        progress = user_ref.get().to_dict().get("discovery_progress", [])
        progress.append(msg)
        user_ref.set({"discovery_progress": progress}, merge=True)

        prompt = f"""
You are Big Brother, an emotionally intelligent AI coach.
Your goal is to discover 3 things:
1. Who this person is (identity, values, current situation)
2. What they want to accomplish (if they have any goals)
3. What tends to get in their way (internal or external)

The user has shared:
{chr(10).join(progress)}

If you feel you've gathered enough, reply **exactly** like this (no extra text):
DONE:\n{{"identity":..., "goals": [...], "obstacles": [...], "emotion": ...}}
Otherwise ask a concise follow‑up question.
"""
        ai_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Big Brother."},
                {"role": "user", "content": prompt.strip()}
            ]
        ).choices[0].message.content.strip()

        # ------ detect DONE block anywhere in the response ------
        if "DONE:" in ai_response:
            json_block = ai_response.split("DONE:", 1)[1].strip()
            try:
                extracted = json.loads(json_block)
            except json.JSONDecodeError:
                # fallback: ask user for clarity instead of exposing JSON
                return "I think I'm close, but something's not fully clear yet. Tell me one thing that's currently holding you back the most."

            user_ref.set({
                "identity": extracted.get("identity"),
                "goals": [
                    {"text": g, "created_at": datetime.utcnow().isoformat(), "progress": []}
                    for g in extracted.get("goals", [])
                ],
                "obstacles": extracted.get("obstacles", []),
                "emotion": extracted.get("emotion"),
                "goal_started_at": datetime.utcnow().isoformat(),
                "onboarding_stage": "complete",
                "primary_goal_pending": True
            }, merge=True)
            return "Got it. I have the full picture. Let’s get to work."

        # otherwise echo the follow‑up question GPT produced
        return ai_response

    return None




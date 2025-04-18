from datetime import datetime

def handle_onboarding(stage, msg, user_ref, client):
    # Reset legacy or malformed onboarding stages
    if stage not in [0, "dynamic"]:
        user_ref.set({"onboarding_stage": "dynamic", "discovery_progress": []}, merge=True)
        intro = "Welcome to Big Brother AI. Thank you for taking the next step in your self-improvement journey. I'm here to help you achieve more, stress less, and live a happier, fuller life. You're here because you want something greater — I’m here to walk alongside you and keep you grounded in that mission. I’ll be honest with you, I’ll hold you to your word, and I’ll have your back every step of the way."
        return f"{intro}\n\nLet’s start with something simple: What is your name and what do you do?"

    if stage == 0:
        user_ref.set({"onboarding_stage": "dynamic", "discovery_progress": []}, merge=True)
        intro = "Welcome to Big Brother AI. Thank you for taking the next step in your self-improvement journey. I'm here to help you achieve more, stress less, and live a happier, fuller life. You're here because you want something greater — I’m here to walk alongside you and keep you grounded in that mission. I’ll be honest with you, I’ll hold you to your word, and I’ll have your back every step of the way."
        return f"{intro}\n\nLet’s start with something simple: What is your name and what do you do?"

    if stage == "dynamic":
        progress = user_ref.get().to_dict().get("discovery_progress", [])
        progress.append(msg)
        user_ref.set({"discovery_progress": progress}, merge=True)

        if len(progress) < 3:
            prompt = f"""
You are Big Brother, an emotionally intelligent AI coach.
You are currently onboarding a new user through open conversation.
Your goal is to discover 3 things:
1. Who this person is (identity, values, current situation)
2. What they want to accomplish (if they have any goals)
3. What tends to get in their way (internal or external)

The user has shared:
{chr(10).join(progress)}

If you feel you’ve gathered enough to proceed, reply with:
DONE:
{{"identity": ..., "goals": [...], "obstacles": [...], "emotion": ...}}

Otherwise, ask a follow-up question to gently guide them deeper.
"""
            ai_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are Big Brother."},
                    {"role": "user", "content": prompt.strip()}
                ]
            ).choices[0].message.content.strip()

            if ai_response.startswith("DONE:"):
                import json
                extracted = json.loads(ai_response.replace("DONE:", "").strip())
                user_ref.set({
                    "identity": extracted.get("identity"),
                    "goals": [{"text": g, "created_at": datetime.utcnow().isoformat(), "progress": []} for g in extracted.get("goals", [])],
                    "obstacles": extracted.get("obstacles", []),
                    "emotion": extracted.get("emotion"),
                    "goal_started_at": datetime.utcnow().isoformat(),
                    "onboarding_stage": "complete",
                    "primary_goal_pending": True
                }, merge=True)
                return "Got it. You’re locked in. Let’s get to work."
            else:
                return ai_response

        return "Tell me more. I’m listening."

    return None


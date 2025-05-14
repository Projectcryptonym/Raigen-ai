from google.cloud import firestore

db = firestore.Client()

def generate_30_day_plan(user_id):
    doc = db.collection("user_profiles").document(user_id).get()
    if not doc.exists:
        return {"error": "User not found."}

    data = doc.to_dict()
    energy = data["current_self"]["energy_state"]
    friction = data["current_self"]["stuck_pattern"]
    morning = data["highest_self"]["morning_routine"]
    shift = data["highest_self"]["proud_shift"]

    # Simple templated plan (can be replaced with GPT later)
    plan = {
        "day_1": f"Write down your current morning routine and compare it to this: '{morning}'",
        "day_2": f"Do a 5-minute action that moves you toward '{shift}'",
        "day_3": f"Reflect on what makes '{friction}' hard to face. Just write it.",
        "day_4": "Protect 30 minutes of your day. Don't negotiate with it.",
        "day_5": f"Visualize who no longer tolerates '{data['highest_self']['non_negotiables']}' — and act like them for 10 minutes.",
        "day_6": "Walk, journal, or sit in silence. No distractions. Just observe.",
        "day_7": "Rest and review. What did you actually do this week?"
    }

    db.collection("coaching_plans").document(user_id).set({
        "user_id": user_id,
        "plan": plan
    })

    return {"message": "Plan created.", "plan": plan}

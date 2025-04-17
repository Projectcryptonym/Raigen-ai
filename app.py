from flask import Flask, request
from twilio.rest import Client
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from datetime import datetime

app = Flask(__name__)

# Environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON")

# Initialize clients
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)
cred = credentials.Certificate(json.loads(FIREBASE_CREDENTIALS_JSON))
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/")
def home():
    return "Big Brother AI Backend is Running ✅"

@app.route("/sms", methods=["POST"])
def sms_reply():
    try:
        incoming_msg = request.form["Body"]
        sender = request.form["From"]

        print(f"[Incoming SMS] From: {sender} | Message: {incoming_msg}")

        user_ref = db.collection("users").document(sender)
        user_doc = user_ref.get()
        user_data = user_doc.to_dict() if user_doc.exists else {}

        # Determine Big Brother mood based on recent behavior
        mood = "neutral"
        if user_data.get("streak_days", 0) >= 10:
            mood = "locked-in"
        elif user_data.get("wins", 0) >= 5:
            mood = "respectful"
        elif user_data.get("silence_ping_count", 0) >= 3:
            mood = "cold"
        elif user_data.get("clarity_push_count", 0) >= 2:
            mood = "frustrated"

        if incoming_msg.strip().lower() in ["stop", "unsubscribe", "cancel", "leave me alone"]:
            user_ref.set({"opted_out": True}, merge=True)
            twilio_client.messages.create(
                body="Understood. You won’t receive any more messages. If you change your mind, just say 'START'.",
                from_=TWILIO_PHONE_NUMBER,
                to=sender
            )
            return "Opt-out confirmed", 200

        if user_data.get("paused"):
            print(f"[Paused User] {sender} is paused. Ignoring until reengaged.")
            return "User paused", 200

        if user_data.get("opted_out"):
            print(f"[Opted Out] {sender} is opted out. Ignoring message.")
            return "User opted out", 200

        onboarding_stage = user_data.get("onboarding_stage", 0)

        if onboarding_stage == 0:
            user_ref.set({"onboarding_stage": 1}, merge=True)
            intro_text = (
                "Welcome to Big Brother AI. Let’s keep this simple and real. I’m here to help you become the best version of yourself — the one you know you’re capable of becoming."
            )
            question = "Let’s start simple: Who are you and what’s going on in your life right now?"
            reply = f"{intro_text}\n\n{question}"
        elif onboarding_stage == 1:
            eval_prompt = f"The user was asked to describe who they are. They said: '{incoming_msg}'. Is this a clear, honest, coaching-grade answer? Reply only 'yes' or 'no'."
            evaluation = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a clarity evaluator for an AI coach."},
                    {"role": "user", "content": eval_prompt}
                ]
            )
            verdict = evaluation.choices[0].message.content.strip().lower()
            if verdict.startswith("no"):
                reply = "Don’t waste my time. I need to know who you really are if I’m going to help you. Let’s try again — who are you, really?"
            else:
                user_ref.set({"identity": incoming_msg, "onboarding_stage": 2}, merge=True)
                reply = "What are some specific things you want to accomplish or change in the next 30 days?""What are some specific things you want to accomplish or change in the next 30 days?"
        elif onboarding_stage == 2:
            eval_prompt = f"The user was asked to list specific goals. They said: '{incoming_msg}'. Is this a clear, coaching-ready answer? Reply only 'yes' or 'no'."
            evaluation = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a clarity evaluator for an AI coach."},
                    {"role": "user", "content": eval_prompt}
                ]
            )
            verdict = evaluation.choices[0].message.content.strip().lower()
            if verdict.startswith("no"):
                reply = "That’s too vague. I need something more specific to work with. What’s one thing you actually want to improve?"
            else:
                goals = [g.strip() for g in incoming_msg.split(",") if g.strip()]
                goal_objects = [{"text": g, "created_at": datetime.utcnow().isoformat(), "progress": []} for g in goals]
                user_ref.set({"goals": goal_objects, "goal_started_at": datetime.utcnow().isoformat(), "onboarding_stage": 3}, merge=True)
                reply = "What usually gets in your way? Be honest.""What usually gets in your way? Be honest."
        elif onboarding_stage == 3:
            eval_prompt = f"The user was asked what usually gets in their way. They responded: '{incoming_msg}'. Is this a specific, coaching-ready answer or is it vague or broad? Reply only 'yes' or 'no'."
            evaluation = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a clarity evaluator for an AI coach."},
                    {"role": "user", "content": eval_prompt}
                ]
            )
            verdict = evaluation.choices[0].message.content.strip().lower()
            if verdict.startswith("no"):
                reply = "That sounds broad. Let’s go one level deeper. What *specifically* tends to trip you up on a daily basis?"
            else:
                obstacles = [o.strip() for o in incoming_msg.split(",") if o.strip()]
                user_ref.set({"obstacles": obstacles, "onboarding_stage": "complete", "primary_goal_pending": True}, merge=True)
                reply = "Got it. We’re locked in. Let’s get to work.""Got it. We’re locked in. Let’s get to work."
                
        elif user_data.get("why_pending"):
            user_ref.set({"why": incoming_msg, "why_pending": False}, merge=True)
            reply = "That’s powerful. I’ll remember that. Let’s get back to work."
        elif user_data.get("primary_goal_pending"):
            user_ref.set({"primary_goal": incoming_msg, "primary_goal_pending": False}, merge=True)
            reply = "Got it. We’ll use that as your north star for now. Let’s get to work."

        else:
            lower_msg = incoming_msg.lower()

            if any(x in lower_msg for x in ["i failed", "i suck", "i’m a mess", "i can’t", "why bother", "what’s the point"]):
                emotion_state = "ashamed"
            elif any(x in lower_msg for x in ["tired", "burned out", "exhausted", "overwhelmed"]):
                emotion_state = "burned out"
            elif any(x in lower_msg for x in ["i did it", "crushed it", "win", "nailed it"]):
                emotion_state = "victorious"
            elif any(x in lower_msg for x in ["anxious", "worried", "panic", "nervous"]):
                emotion_state = "anxious"
            else:
                emotion_state = "neutral"

            if any(x in lower_msg for x in ["gym", "workout", "run", "lift", "training"]):
                domain_context = "fitness"
            elif any(x in lower_msg for x in ["food", "eating", "diet", "snack", "binge"]):
                domain_context = "nutrition"
            elif any(x in lower_msg for x in ["money", "budget", "broke", "debt"]):
                domain_context = "finance"
            elif any(x in lower_msg for x in ["focus", "distraction", "procrastinate", "tasks", "overwhelm"]):
                domain_context = "productivity"
            elif any(x in lower_msg for x in ["why", "what’s the point", "purpose", "meaning", "identity"]):
                domain_context = "mindset"
            elif any(x in lower_msg for x in ["i hate myself", "i lied", "i relapsed", "i’m lost"]):
                domain_context = "confession"
            else:
                domain_context = "general"

            coaching_goal = "help the user gain clarity and take action"
            now = datetime.utcnow()
            user_ref.set({"last_interaction": now.isoformat()}, merge=True)
            db.collection("users").document(sender).collection("messages").add({
                "timestamp": now.isoformat(),
                "message": incoming_msg,
                "from_user": True
            })

            user_memory_snippet = ""
            # Strategy recalibration: track recent goal-related messages
            goal_repeats = {}
            for m in message_log:
                msg = m.to_dict().get("message", "").lower()
                for goal in user_data.get("goals", []):
                    goal_text = goal["text"].lower()
                    if goal_text in msg:
                        goal_repeats[goal_text] = goal_repeats.get(goal_text, 0) + 1
            for goal_text, count in goal_repeats.items():
                if count >= 3:
                    memory_lines.append(f"• You’ve been circling '{goal_text}' for a while now. What’s keeping you stuck? Let’s either shift the strategy or cut the excuses — your call.")

            # Weekly reflection if goal started 7+ days ago
            if "goal_started_at" in user_data:
                try:
                    start_date = datetime.fromisoformat(user_data["goal_started_at"])
                    days_since = (now - start_date).days
                    if days_since >= 7:
                        memory_lines.append("• It’s been a week since this goal started. What’s actually working? What’s not? Push forward or shift focus — but make a move.")
                except:
                    pass
            message_log = db.collection("users").document(sender).collection("messages").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5).stream()
            repeated_phrases = []
            for m in message_log:
                content = m.to_dict().get("message", "").lower()
                if any(p in content for p in ["tired", "overwhelmed", "burnout", "relapsed"]):
                    repeated_phrases.append(content)

            if len(repeated_phrases) >= 3:
                memory_lines.append("• Pattern Detected: repeated burnout or emotional struggle — time to reflect deeper.")
            wins = user_data.get("wins", 0)
            if wins >= 3:
                memory_lines.append(f"• Earned Respect: {wins} wins logged — this user is putting in work.")

            streak_days = user_data.get("streak_days")
            if streak_days and streak_days >= 7:
                memory_lines.append(f"• Streak: {streak_days} days active — don’t break momentum.")
            memory_lines = []
            if "goals" in user_data:
                formatted_goals = "; ".join([g["text"] for g in user_data["goals"]])
                memory_lines.append(f"• Goals: {formatted_goals}")
            if "primary_goal" in user_data:
                memory_lines.append(f"• Primary Goal: {user_data['primary_goal']}")
            if "obstacles" in user_data:
                formatted_obstacles = "; ".join(user_data["obstacles"])
                memory_lines.append(f"• Obstacles: {formatted_obstacles}")
            if "identity" in user_data:
                memory_lines.append(f"• Identity: {user_data['identity']}")
            if "why" in user_data:
                memory_lines.append(f"• Why: {user_data['why']}")
            user_memory_snippet = "\n".join(memory_lines)

            if emotion_state in ["ashamed", "burned out", "victorious"] and not user_data.get("why"):
                user_ref.set({"why_pending": True}, merge=True)
                reply = "Before we go further… why does this matter to you? Like really matter."
            else:
                from datetime import datetime, timezone
...
local_hour = datetime.now(timezone.utc).astimezone().hour
if local_hour < 7:
    time_context = "early morning"
elif 7 <= local_hour < 12:
    time_context = "morning"
elif 12 <= local_hour < 18:
    time_context = "afternoon"
elif 18 <= local_hour < 22:
    time_context = "evening"
else:
    time_context = "late night"
...
prompt = f"""
You are Big Brother — the older, wiser brother with emotional intelligence who always tells the truth. You’re here to keep this user focused, grounded, and honest. One consistent voice. Adaptive delivery. No sugarcoating.

Context:
• Emotion: {emotion_state}
• Domain: {domain_context}
• Mood: {mood}
• Goal: {coaching_goal}
• Time: {time_context}
• Emotion: {emotion_state}
• Domain: {domain_context}
• Goal: {coaching_goal}
• Time: {time_context}

Memory:
{user_memory_snippet}

Incoming Message:
{incoming_msg}

Respond with emotional intelligence and clarity. You can challenge, reflect, affirm, or redirect — but always as the same voice.
If the message feels genuine, feel it. If it deserves challenge, give it. Don't pretend. Be real."""
{incoming_msg}

Respond with emotional intelligence and clarity. You can challenge, reflect, affirm, or redirect — but always as the same voice.
"""
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are Big Brother."},
                        {"role": "user", "content": prompt}
                    ]
                )
                reply = response.choices[0].message.content.strip()

                db.collection("users").document(sender).collection("messages").add({
                    "timestamp": now.isoformat(),
                    "message": reply,
                    "from_user": False
                })

        twilio_client.messages.create(
            body=reply,
            from_=TWILIO_PHONE_NUMBER,
            to=sender
        )

        print(f"[Reply Sent] To: {sender} | Message: {reply}")
        return "OK", 200

    except Exception as e:
        print(f"[Error] {str(e)}")
        return str(e), 500



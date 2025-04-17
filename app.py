from flask import Flask, request
from twilio.rest import Client
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from datetime import datetime, timezone

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
def handle_onboarding(stage, msg, user_ref, client):
    if stage == 0:
        user_ref.set({"onboarding_stage": 1}, merge=True)
        intro = "Welcome to Big Brother AI. Let's keep this simple and real. I'm here to help you become the best version of yourself - the one you know you're capable of becoming."
        return f"{intro}\\n\\nLet's start simple: Who are you and what's going on in your life right now?"

Let's start simple: Who are you and what's going on in your life right now?"

    if stage == 1:
        prompt = f"The user was asked to describe who they are. They said: '{msg}'. Is this a clear, honest, coaching-grade answer? Reply only 'yes' or 'no'."
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a clarity evaluator for an AI coach."},
                {"role": "user", "content": prompt}
            ]
        )
        verdict = result.choices[0].message.content.strip().lower()
        if verdict.startswith("no"):
            return "Don't waste my time. I need to know who you really are if I'm going to help you. Let's try again - who are you, really?"
        else:
            user_ref.set({"identity": msg, "onboarding_stage": 2}, merge=True)
            return "What are some specific things you want to accomplish or change in the next 30 days?"

    if stage == 2:
        prompt = f"The user was asked to list specific goals. They said: '{msg}'. Is this a clear, coaching-ready answer? Reply only 'yes' or 'no'."
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a clarity evaluator for an AI coach."},
                {"role": "user", "content": prompt}
            ]
        )
        verdict = result.choices[0].message.content.strip().lower()
        if verdict.startswith("no"):
            return "That's too vague. I need something more specific to work with. What's one thing you actually want to improve?"
        else:
            goals = [g.strip() for g in msg.split(",") if g.strip()]
            goal_objects = [{"text": g, "created_at": datetime.utcnow().isoformat(), "progress": []} for g in goals]
            user_ref.set({"goals": goal_objects, "goal_started_at": datetime.utcnow().isoformat(), "onboarding_stage": 3}, merge=True)
            return "What usually gets in your way? Be honest."

    if stage == 3:
        prompt = f"The user was asked what usually gets in their way. They responded: '{msg}'. Is this a specific, coaching-ready answer or is it vague or broad? Reply only 'yes' or 'no'."
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a clarity evaluator for an AI coach."},
                {"role": "user", "content": prompt}
            ]
        )
        verdict = result.choices[0].message.content.strip().lower()
        if verdict.startswith("no"):
            return "That sounds broad. Let's go one level deeper. What specifically tends to trip you up on a daily basis?"
        else:
            obstacles = [o.strip() for o in msg.split(",") if o.strip()]
            user_ref.set({"obstacles": obstacles, "onboarding_stage": "complete", "primary_goal_pending": True}, merge=True)
            return "Got it. We're locked in. Let's get to work."

    return None

def build_prompt(emotion, domain, mood, goal, time, memory, message):
    return f"""
You are Big Brother - the older, wiser brother with emotional intelligence who always tells the truth. You’re here to keep this user focused, grounded, and honest. One consistent voice. Adaptive delivery. No sugarcoating.

Context:
• Emotion: {emotion}
• Domain: {domain}
• Mood: {mood}
• Goal: {goal}
• Time: {time}

Memory:
{memory}

Incoming Message:
{message}

Respond with emotional intelligence and clarity. You can challenge, reflect, affirm, or redirect - but always as the same voice.
If the message feels genuine, feel it. If it deserves challenge, give it. Don't pretend. Be real.
"""

def call_big_brother(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are Big Brother."},
            {"role": "user", "content": prompt}
        ]
    )
    return response

@app.route("/sms", methods=["POST"])
def sms_reply():
    try:
        incoming_msg = request.form["Body"]
        sender = request.form["From"]

        print(f"[Incoming SMS] From: {sender} | Message: {incoming_msg}")

        user_ref = db.collection("users").document(sender)
        user_doc = user_ref.get()
        user_data = user_doc.to_dict() if user_doc.exists else {}

        if user_data.get("opted_out"):
            print(f"[Opted Out] {sender} is opted out. Ignoring message.")
            return "User opted out", 200

        if incoming_msg.strip().lower() in ["stop", "unsubscribe", "cancel", "leave me alone"]:
            user_ref.set({"opted_out": True}, merge=True)
            twilio_client.messages.create(
                body="Understood. You won’t receive any more messages. If you change your mind, just say 'START'.",
                from_=TWILIO_PHONE_NUMBER,
                to=sender
            )
            return "Opt-out confirmed", 200

        onboarding_stage = user_data.get("onboarding_stage", 0)
        reply = handle_onboarding(onboarding_stage, incoming_msg, user_ref, client)
        if reply:
            twilio_client.messages.create(
                body=reply,
                from_=TWILIO_PHONE_NUMBER,
                to=sender
            )
            return "OK", 200

        if user_data.get("why_pending"):
            user_ref.set({"why": incoming_msg, "why_pending": False}, merge=True)
            reply = "That’s powerful. I’ll remember that. Let’s get back to work."
            twilio_client.messages.create(body=reply, from_=TWILIO_PHONE_NUMBER, to=sender)
            return "OK", 200

        if user_data.get("primary_goal_pending"):
            user_ref.set({"primary_goal": incoming_msg, "primary_goal_pending": False}, merge=True)
            reply = "Got it. We’ll use that as your north star for now. Let’s get to work."
            twilio_client.messages.create(body=reply, from_=TWILIO_PHONE_NUMBER, to=sender)
            return "OK", 200

        emotion_state, domain_context = classify_emotion_and_domain(incoming_msg.lower())

        now = datetime.utcnow()
        user_ref.set({"last_interaction": now.isoformat()}, merge=True)
        db.collection("users").document(sender).collection("messages").add({
            "timestamp": now.isoformat(),
            "message": incoming_msg,
            "from_user": True
        })

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

        mood = user_data.get("mood", "neutral")
        coaching_goal = "help the user gain clarity and take action"
        user_memory_snippet = build_user_memory(user_data)

        prompt = build_prompt(emotion_state, domain_context, mood, coaching_goal, time_context, user_memory_snippet, incoming_msg)
        response = call_big_brother(prompt)
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

def build_user_memory(user_data):
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
    if user_data.get("wins", 0) >= 3:
        memory_lines.append(f"• Earned Respect: {user_data['wins']} wins logged - this user is putting in work.")
    if user_data.get("streak_days", 0) >= 7:
        memory_lines.append(f"• Streak: {user_data['streak_days']} days active - don’t break momentum.")
    return "\n".join(memory_lines)


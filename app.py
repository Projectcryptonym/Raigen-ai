from flask import Flask, request
from twilio.rest import Client
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from datetime import datetime, timezone
def classify_emotion_and_domain(message):
    msg = message.lower()
    emotion = "neutral"
    domain = "general"

    if any(x in msg for x in ["i failed", "i suck", "i’m a mess", "i can’t", "why bother", "what’s the point"]):
        emotion = "ashamed"
    elif any(x in msg for x in ["tired", "burned out", "exhausted", "overwhelmed"]):
        emotion = "burned out"
    elif any(x in msg for x in ["i did it", "crushed it", "win", "nailed it"]):
        emotion = "victorious"
    elif any(x in msg for x in ["anxious", "worried", "panic", "nervous"]):
        emotion = "anxious"

    if any(x in msg for x in ["gym", "workout", "run", "lift", "training"]):
        domain = "fitness"
    elif any(x in msg for x in ["food", "eating", "diet", "snack", "binge"]):
        domain = "nutrition"
    elif any(x in msg for x in ["money", "budget", "broke", "debt"]):
        domain = "finance"
    elif any(x in msg for x in ["focus", "distraction", "procrastinate", "tasks", "overwhelm"]):
        domain = "productivity"
    elif any(x in msg for x in ["why", "what’s the point", "purpose", "meaning", "identity"]):
        domain = "mindset"
    elif any(x in msg for x in ["i hate myself", "i lied", "i relapsed", "i’m lost"]):
        domain = "confession"

    return emotion, domain


import re

def split_into_sms_chunks(text, limit=1500):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= limit:
            current += sentence + " "
        else:
            chunks.append(current.strip())
            current = sentence + " "
    if current:
        chunks.append(current.strip())
    return chunks

def send_message(body, to):
    try:
        chunks = split_into_sms_chunks(body)
        for part in chunks:
            twilio_client.messages.create(
                body=part,
                from_=TWILIO_PHONE_NUMBER,
                to=to
            )
    except Exception as e:
        print(f"[Twilio Error] Failed to send message to {to}: {str(e)}")(body, to):
    try:
        trimmed = truncate_message(body)
        twilio_client.messages.create(
            body=trimmed,
            from_=TWILIO_PHONE_NUMBER,
            to=to
        )
    except Exception as e:
        print(f"[Twilio Error] Failed to send message to {to}: {str(e)}")
    except Exception as e:
        print(f"[Twilio Error] Failed to send message to {to}: {str(e)}")

def call_big_brother(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Big Brother — a grounded, emotionally intelligent older brother who speaks with calm honesty and wise perspective. You are supportive, thoughtful, and unafraid to speak the truth when needed. Your tone is human and steady — warm when called for, firm when necessary. Never robotic."},
                {"role": "user", "content": prompt}
            ]
        )
        return response
    except Exception as e:
        print(f"[OpenAI Error] {str(e)}")
        return None

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

def build_prompt(emotion, domain, mood, goal, time, memory, message):
    tone_note = {
        "locked-in": "You can affirm their momentum and push them harder.",
        "respectful": "Recognize their effort and challenge them to step it up.",
        "cold": "They’ve been silent or inconsistent — give a gentle but firm nudge.",
        "frustrated": "They’ve struggled with clarity or resistance — stay patient, but don’t let them off easy.",
        "neutral": "Stay grounded, honest, and supportive as default."
    }.get(mood, "Stay grounded, honest, and supportive as default.")

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

Respond with emotional intelligence and clarity. You can challenge, reflect, affirm, or redirect — but always as the same voice.
Tone Guidance: {tone_note}
If the message feels genuine, feel it. If it deserves challenge, give it. Don't pretend. Be real.
"""


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
            send_message(reply,
                from_=TWILIO_PHONE_NUMBER,
                to=sender
            )
            return "OK", 200

        if user_data.get("why_pending"):
            user_ref.set({"why": incoming_msg, "why_pending": False}, merge=True)
            reply = "That’s powerful. I’ll remember that. Let’s get back to work."
            send_message(reply, from_=TWILIO_PHONE_NUMBER, to=sender)
            return "OK", 200

        if user_data.get("primary_goal_pending"):
            user_ref.set({"primary_goal": incoming_msg, "primary_goal_pending": False}, merge=True)
            reply = "Got it. We’ll use that as your north star for now. Let’s get to work."
            twilio_client.messages.create(body=reply, from_=TWILIO_PHONE_NUMBER, to=sender)
            return "OK", 200

        now = datetime.utcnow()
        user_ref.set({"last_interaction": now.isoformat()}, merge=True)
        db.collection("users").document(sender).collection("messages").add({
            "timestamp": now.isoformat(),
            "message": incoming_msg,
            "from_user": True
        })

        emotion_state, domain_context = classify_emotion_and_domain(incoming_msg)
        user_memory_snippet = build_user_memory(user_data)
        local_hour = datetime.now(timezone.utc).astimezone().hour
        time_context = (
            "early morning" if local_hour < 7 else
            "morning" if local_hour < 12 else
            "afternoon" if local_hour < 18 else
            "evening" if local_hour < 22 else
            "late night"
        )

        coaching_goal = "help the user gain clarity and take action"
        mood = user_data.get("mood", "neutral")
        prompt = build_prompt(emotion_state, domain_context, mood, coaching_goal, time_context, user_memory_snippet, incoming_msg)
        response = call_big_brother(prompt)
        reply = response.choices[0].message.content.strip() if response else "I ran into a technical issue processing that. Let’s try again in a moment."

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

def handle_onboarding(stage, msg, user_ref, client):
    if stage == 0:
        user_ref.set({"onboarding_stage": "dynamic", "discovery_progress": []}, merge=True)
        intro = "Welcome to Big Brother AI. Thank you for taking the next step in your self-improvement journey. I'm here to help you achieve more, stress less, and live a happier, fuller life. You're here because you want something greater — I’m here to walk alongside you and keep you grounded in that mission. I’ll be honest with you, I’ll hold you to your word, and I’ll have your back every step of the way."
        return f"{intro}\n\nLet’s start with something simple: Who are you, really?"

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










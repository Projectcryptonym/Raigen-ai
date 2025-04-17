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

        if incoming_msg.strip().lower() in ["stop", "unsubscribe", "cancel", "leave me alone"]:
            user_ref.set({"opted_out": True}, merge=True)
            twilio_client.messages.create(
                body="Understood. You won’t receive any more messages. If you change your mind, just say 'START'.",
                from_=TWILIO_PHONE_NUMBER,
                to=sender
            )
            return "Opt-out confirmed", 200

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
            user_ref.set({"identity": incoming_msg, "onboarding_stage": 2}, merge=True)
            reply = "What are some specific things you want to accomplish or change in the next 30 days?"
        elif onboarding_stage == 2:
            goals = [g.strip() for g in incoming_msg.split(",") if g.strip()]
            user_ref.set({"goals": goals, "onboarding_stage": 3}, merge=True)
            reply = "What usually gets in your way? Be honest."
        elif onboarding_stage == 3:
            obstacles = [o.strip() for o in incoming_msg.split(",") if o.strip()]
            user_ref.set({"obstacles": obstacles, "onboarding_stage": 4}, merge=True)
            reply = "When I check in with you, do you want blunt honesty or more encouragement and support?"
        elif onboarding_stage == 4:
            user_ref.set({"tone_preference": incoming_msg, "onboarding_stage": "complete"}, merge=True)
            reply = "Got it. We’re locked in. I’ll be keeping an eye on you. Let’s go."
        elif user_data.get("why_pending"):
            user_ref.set({"why": incoming_msg, "why_pending": False}, merge=True)
            reply = "That’s powerful. I’ll remember that. Let’s get back to work."
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

            user_memory_snippet = ""
            memory_lines = []
            if "goals" in user_data:
                formatted_goals = "; ".join(user_data["goals"])
                memory_lines.append(f"• Goals: {formatted_goals}")
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
                prompt = f"""
You are Big Brother — the older, wiser brother with emotional intelligence who always tells the truth. You’re here to keep this user focused, grounded, and honest. One consistent voice. Adaptive delivery. No sugarcoating.

Context:
• Emotion: {emotion_state}
• Domain: {domain_context}
• Goal: {coaching_goal}

Memory:
{user_memory_snippet}

Message:
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

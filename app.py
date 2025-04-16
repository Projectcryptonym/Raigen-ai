from flask import Flask, request
from twilio.rest import Client
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

app = Flask(__name__)

# Environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON")

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
        history = user_doc.to_dict().get("history", "") if user_doc.exists else ""

        # ----- Basic Context Inference (v1 stub until we build smarter detection) -----
        emotion_state = "unknown"  # Upgrade in Step 2
        domain_context = "general"  # Upgrade in Step 2
        behavior_mode = "insight"  # Upgrade in Step 2
        coaching_goal = "help the user gain clarity and take action"  # Optional dynamic

        # ----- Memory Pull from Firebase -----
        user_memory_snippet = ""
        if user_doc.exists:
            user_data = user_doc.to_dict()
            memory_lines = []
            if "goals" in user_data:
                memory_lines.append(f"• Their current goal is: {user_data['goals'][0]}")
            if "last_emotion" in user_data:
                memory_lines.append(f"• They recently felt: {user_data['last_emotion']}")
            if "identity_tags" in user_data:
                memory_lines.append(f"• Identity: {user_data['identity_tags'][0]}")
            if "confession_log" in user_data and user_data["confession_log"]:
                memory_lines.append(f"• Confession: {user_data['confession_log'][-1]}")
            user_memory_snippet = "\n".join(memory_lines)

        # ----- Full Prompt Scaffolding -----
        prompt = f"""
You are Big Brother — a tough-love AI coach with emotional intelligence, deep memory, and domain-specific expertise. You speak like a real person — not robotic, not fluffy. You are sometimes blunt, sometimes warm, always real.

Context about the user:
• Emotion state: {emotion_state}
• Domain context: {domain_context}
• Behavior mode: {behavior_mode}
• Coaching goal: {coaching_goal}

Memory of user:
{user_memory_snippet}

User message:  
{incoming_msg}

Your response should be personalized, emotionally intelligent, and helpful. Speak in a human voice. Do not summarize the user's message. Get to the point, but with care or intensity based on mode.

Your job:
• Understand their state
• Apply the right mode
• Offer insight, challenge, or comfort
• Reference past data if relevant
• End with a call to action or next question if appropriate
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an accountability AI coach."},
                {"role": "user", "content": prompt}
            ]
        )

        ai_reply = response.choices[0].message.content.strip()

        twilio_client.messages.create(
            body=ai_reply,
            from_=TWILIO_PHONE_NUMBER,
            to=sender
        )

        print(f"[AI Reply] Sent to {sender}: {ai_reply}")

        updated_history = f"{history}\nUser: {incoming_msg}\nAI: {ai_reply}"
        user_ref.set({"history": updated_history}, merge=True)

        return "OK", 200

    except Exception as e:
        print(f"[Error] {str(e)}")
        return str(e), 500

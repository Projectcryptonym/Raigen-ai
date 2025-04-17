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
def classify_emotion_and_domain(message):
    message = message.lower()
    emotion = "neutral"
    domain = "general"

    if any(x in message for x in ["i failed", "i suck", "i’m a mess", "i can’t", "why bother", "what’s the point"]):
        emotion = "ashamed"
    elif any(x in message for x in ["tired", "burned out", "exhausted", "overwhelmed"]):
        emotion = "burned out"
    elif any(x in message for x in ["i did it", "crushed it", "win", "nailed it"]):
        emotion = "victorious"
    elif any(x in message for x in ["anxious", "worried", "panic", "nervous"]):
        emotion = "anxious"

    if any(x in message for x in ["gym", "workout", "run", "lift", "training"]):
        domain = "fitness"
    elif any(x in message for x in ["food", "eating", "diet", "snack", "binge"]):
        domain = "nutrition"
    elif any(x in message for x in ["money", "budget", "broke", "debt"]):
        domain = "finance"
    elif any(x in message for x in ["focus", "distraction", "procrastinate", "tasks", "overwhelm"]):
        domain = "productivity"
    elif any(x in message for x in ["why", "what’s the point", "purpose", "meaning", "identity"]):
        domain = "mindset"
    elif any(x in message for x in ["i hate myself", "i lied", "i relapsed", "i’m lost"]):
        domain = "confession"

    return emotion, domain

def build_user_memory(user_data):
    user_memory_snippet = build_user_memory(user_data)


            coaching_goal = "help the user gain clarity and take action"

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


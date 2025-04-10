from flask import Flask, request
from twilio.rest import Client
import openai
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
openai.api_key = OPENAI_API_KEY

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

        # Firestore user history
        user_ref = db.collection("users").document(sender)
        user_doc = user_ref.get()
        history = user_doc.to_dict().get("history", "") if user_doc.exists else ""

        prompt = f"You are an aggressive but supportive accountability coach. Keep responses short and direct.\nUser: {incoming_msg}\nCoach:"

     response = client.chat.completions.create(
    model="gpt-4-turbo",
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
        print(f"[Error] {e}")
        return str(e), 500


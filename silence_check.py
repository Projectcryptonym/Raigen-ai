from twilio.rest import Client
from firebase_admin import firestore
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials
import os
import json

# Environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")
FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON")

# Initialize Twilio and Firebase
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
cred = credentials.Certificate(json.loads(FIREBASE_CREDENTIALS_JSON))
firebase_admin.initialize_app(cred)
db = firestore.client()

def send_silence_pings():
    now = datetime.utcnow()
    silence_threshold = now - timedelta(hours=48)
    
    users_ref = db.collection("users")
    users = users_ref.stream()

    for user in users:
        data = user.to_dict()
        phone = user.id

        if data.get("onboarding_stage") != "complete":
            continue
        if data.get("opted_out") == True:
            continue

        silence_count = data.get("silence_ping_count", 0)

        last = data.get("last_interaction")
        if not last:
            continue

        last_dt = datetime.fromisoformat(last)
        if last_dt < silence_threshold:
            print(f"[Silence] {phone} has been quiet since {last_dt}")
            import random

            messages = [
                "You’ve been quiet. That usually means something’s off. Want to talk?",
                "You disappeared. What happened? I’m still here if you’re ready.",
                "Silence speaks volumes. You good?",
                "If you’re stuck, say so. That’s what I’m here for.",
                "The version of you that wants change is waiting. Let’s move."
            ]

            msg = random.choice(messages)
            if silence_count >= 3:
                why = data.get("why") or data.get("identity") or "what lit your fire in the first place"
                msg = f"You’ve ignored me 3 times. Don’t forget what lit your fire: {why}. Let’s get back to it."

            twilio_client.messages.create(
                body=msg,
                from_=TWILIO_PHONE_NUMBER,
                to=phone
            )

            db.collection("users").document(phone).set({"silence_ping_count": silence_count + 1}, merge=True)

if __name__ == "__main__":
    send_silence_pings()

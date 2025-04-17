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

        last = data.get("last_interaction")
        if not last:
            continue

        last_dt = datetime.fromisoformat(last)
        if last_dt < silence_threshold:
            print(f"[Silence] {phone} has been quiet since {last_dt}")
            twilio_client.messages.create(
                body="You’ve been quiet. That usually means something’s off. Want to talk?",
                from_=TWILIO_PHONE_NUMBER,
                to=phone
            )

if __name__ == "__main__":
    send_silence_pings()

from datetime import datetime, timedelta
import os
import firebase_admin
from firebase_admin import credentials, firestore
from twilio.rest import Client
import json

# Load environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")
FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON")

# Initialize services
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
cred = credentials.Certificate(json.loads(FIREBASE_CREDENTIALS_JSON))
firebase_admin.initialize_app(cred)
db = firestore.client()

now = datetime.utcnow()
cutoff = now - timedelta(hours=48)

users = db.collection("users").stream()
for user in users:
    data = user.to_dict()
    phone = user.id

    if data.get("opted_out") or data.get("paused"):
        continue

    last = data.get("last_interaction")
    if not last:
        continue

    last_time = datetime.fromisoformat(last)
    if last_time > cutoff:
        continue

    ping_count = data.get("silence_ping_count", 0)

    if ping_count >= 3:
        db.collection("users").document(phone).set({"paused": True}, merge=True)
        twilio_client.messages.create(
            body="You’ve been quiet for a while. I won’t chase you — but I’m still here when you’re ready to show up.",
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
    else:
        twilio_client.messages.create(
            body="Haven’t heard from you. You still in this, or are we slipping again?",
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        db.collection("users").document(phone).set({"silence_ping_count": ping_count + 1}, merge=True)


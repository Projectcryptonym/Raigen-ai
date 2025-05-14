# sms_webhook.py

from flask import Blueprint, request, Response
from google.cloud import firestore
from intent_router import route_intent
import intent_handlers as handlers

sms_bp = Blueprint("sms", __name__)
db = firestore.Client()

@sms_bp.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body", "").strip()
    user_phone = request.form.get("From", "").strip()

    # Fetch user doc (optional state use later)
    user_doc = db.collection("users").document(user_phone).get()
    user_state = user_doc.to_dict() if user_doc.exists else {}

    # Classify and dispatch
    intent, handler_func = route_intent(incoming_msg, user_state)
    handler = getattr(handlers, handler_func, handlers.handle_unknown)

    return Response(handler(user_phone), mimetype="application/xml")



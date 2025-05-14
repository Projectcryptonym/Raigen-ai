# onboarding_api.py

from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime

onboarding_bp = Blueprint("onboarding", __name__)
db = firestore.client()

@onboarding_bp.route("/onboarding", methods=["POST"])
def onboarding_webhook():
    try:
        data = request.get_json()

        # Replace with how you identify the user (e.g., phone, email, ID field from form)
        user_id = data.get("phone") or data.get("email") or "anonymous_" + datetime.utcnow().isoformat()

        doc_ref = db.collection("users").document(user_id)
        doc_ref.set({
            "tier1_complete": True,
            "tier1_data": data,
            "updated_at": datetime.utcnow()
        }, merge=True)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"[ERROR] Onboarding webhook failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


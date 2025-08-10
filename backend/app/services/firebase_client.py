import base64, json, firebase_admin
from firebase_admin import credentials, firestore
from functools import lru_cache
import os

@lru_cache()
def get_db():
    b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_BASE64")
    if not b64:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON_BASE64 missing")
    info = json.loads(base64.b64decode(b64).decode("utf-8"))
    cred = credentials.Certificate(info)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {'projectId': os.getenv("FIREBASE_PROJECT_ID")})
    return firestore.client() 
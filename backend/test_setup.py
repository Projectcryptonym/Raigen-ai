#!/usr/bin/env python3
"""
Test script to verify backend setup
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all required modules can be imported"""
    try:
        from app.services.firebase_client import get_db
        print("✅ Firebase client imports successfully")
    except Exception as e:
        print(f"❌ Firebase client import failed: {e}")
        return False
    
    try:
        from app.services.google_calendar import list_events, upsert_event
        print("✅ Google Calendar service imports successfully")
    except Exception as e:
        print(f"❌ Google Calendar service import failed: {e}")
        return False
    
    try:
        from app.services.memos import memory_store, memory_search
        print("✅ Memory API service imports successfully")
    except Exception as e:
        print(f"❌ Memory API service import failed: {e}")
        return False
    
    try:
        from app.routes.auth import router as auth_router
        from app.routes.calendar import router as calendar_router
        from app.routes.plan import router as plan_router
        print("✅ All route modules import successfully")
    except Exception as e:
        print(f"❌ Route import failed: {e}")
        return False
    
    return True

def test_env_vars():
    """Test that required environment variables are set"""
    required_vars = [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET", 
        "GOOGLE_REDIRECT_URI",
        "FIREBASE_PROJECT_ID",
        "FIREBASE_SERVICE_ACCOUNT_JSON_BASE64"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    print("🧪 Testing Raigen Backend Setup...")
    print("=" * 50)
    
    env_ok = test_env_vars()
    imports_ok = test_imports()
    
    print("=" * 50)
    if env_ok and imports_ok:
        print("🎉 All tests passed! Backend is ready to run.")
        print("\nNext steps:")
        print("1. Run: cd backend && uvicorn app.main:app --reload --port 8080")
        print("2. Test OAuth: curl http://localhost:8080/auth/google/url")
        print("3. Test health: curl http://localhost:8080/health")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 
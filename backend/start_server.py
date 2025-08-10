#!/usr/bin/env python3
"""
Startup script for Raigen Backend with default test values
"""
import os
import sys

# Set default test environment variables if not already set
defaults = {
    "APP_ENV": "dev",
    "PORT": "8080",
    "GOOGLE_CLIENT_ID": "test-client-id",
    "GOOGLE_CLIENT_SECRET": "test-client-secret", 
    "GOOGLE_REDIRECT_URI": "http://localhost:8080/auth/google/callback",
    "FIREBASE_PROJECT_ID": "test-project-id",
    "FIREBASE_SERVICE_ACCOUNT_JSON_BASE64": "eyJ0eXBlIjoidGVzdCIsInByb2plY3RfaWQiOiJ0ZXN0In0=",
    "OPENAI_API_KEY": "test-key",
    "OPENAI_MODEL_GPT5": "gpt-5",
    "OPENAI_MODEL_ROUTER": "gpt-4o-mini",
    "ELEVENLABS_API_KEY": "test-key",
    "ELEVENLABS_VOICE_ID": "test-voice-id",
    "STRIPE_SECRET_KEY": "test-key"
}

for key, value in defaults.items():
    if not os.getenv(key):
        os.environ[key] = value
        print(f"Set {key} to default value")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Raigen Backend...")
    print("📝 Using test environment variables")
    print("🌐 Server will be available at: http://localhost:8080")
    print("📚 API docs at: http://localhost:8080/docs")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1) 
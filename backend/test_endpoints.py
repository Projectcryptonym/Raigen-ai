#!/usr/bin/env python3
"""
Test script for Raigen Backend endpoints
"""
import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Test an endpoint and return the result"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ Unknown method: {method}")
            return False
            
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - Status: {response.status_code}")
            if response.content:
                try:
                    result = response.json()
                    print(f"   Response: {json.dumps(result, indent=2)}")
                except:
                    print(f"   Response: {response.text}")
            return True
        else:
            print(f"❌ {method} {endpoint} - Expected {expected_status}, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Request failed: {e}")
        return False

def main():
    print("🧪 Testing Raigen Backend Endpoints...")
    print("=" * 60)
    
    # Test basic endpoints
    print("\n📋 Basic Endpoints:")
    test_endpoint("GET", "/")
    test_endpoint("GET", "/health")
    
    # Test OAuth endpoints
    print("\n🔐 OAuth Endpoints:")
    test_endpoint("GET", "/auth/google/url")
    
    # Test plan endpoints
    print("\n📅 Plan Endpoints:")
    test_endpoint("GET", "/plan/today")
    test_endpoint("POST", "/plan/generate")
    test_endpoint("POST", "/plan/replan")
    
    # Test calendar endpoints (will fail with test credentials)
    print("\n📅 Calendar Endpoints (expected to fail with test credentials):")
    test_endpoint("GET", "/calendar/sync?user_id=test-user-1&days=14", expected_status=400)
    
    block_data = {
        "user_id": "test-user-1",
        "title": "Deep Work",
        "start_iso": "2025-08-11T13:00:00Z",
        "end_iso": "2025-08-11T15:00:00Z"
    }
    test_endpoint("POST", "/calendar/block", data=block_data, expected_status=400)
    
    # Test OAuth callback (will fail with test code)
    print("\n🔄 OAuth Callback (expected to fail with test code):")
    callback_data = {
        "code": "test-code",
        "user_id": "test-user-1"
    }
    test_endpoint("POST", "/auth/google/callback", data=callback_data, expected_status=400)
    
    print("\n" + "=" * 60)
    print("🎉 Endpoint testing complete!")
    print("\n📝 Summary:")
    print("- Basic endpoints (/, /health) should work ✅")
    print("- OAuth URL generation should work ✅")
    print("- Plan endpoints should work ✅")
    print("- Calendar/Firebase endpoints will fail with test credentials (expected) ⚠️")
    print("\n🚀 To test with real credentials:")
    print("1. Update .env with real Google OAuth and Firebase credentials")
    print("2. Restart the server")
    print("3. Run this test script again")

if __name__ == "__main__":
    main() 
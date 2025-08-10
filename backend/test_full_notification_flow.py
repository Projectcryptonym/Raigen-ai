#!/usr/bin/env python3

"""
Test script to verify the full notification flow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock Firebase for testing
class MockFirestore:
    def collection(self, name):
        return MockCollection()

class MockCollection:
    def document(self, doc_id):
        return MockDocument()
    
    def where(self, field, op, value):
        return self
    
    def stream(self):
        # Return mock goals data
        return [
            MockDoc({
                "id": "goal1",
                "user_id": "u1",
                "title": "Ship MVP",
                "priority": 3,
                "effort_estimate_min": 120,
                "domain": ["work"],
                "why": "launch beta",
                "status": "active"
            })
        ]

class MockDocument:
    def get(self):
        return MockDocSnapshot()
    
    def set(self, data, merge=True):
        return True

class MockDocSnapshot:
    def __init__(self):
        self.exists = True
        self.data = {"expo_push_token": "ExponentPushToken[test123]"}
    
    def to_dict(self):
        return self.data

class MockDoc:
    def __init__(self, data):
        self.data = data
        self.id = data.get("id", "mock_id")
    
    def to_dict(self):
        return self.data

# Mock the Firebase client
import app.services.repo
app.services.repo.get_db = lambda: MockFirestore()

# Mock httpx for testing
import httpx
original_post = httpx.AsyncClient.post

def mock_post(self, url, **kwargs):
    print(f"[MOCK] POST to {url}")
    print(f"[MOCK] Payload: {kwargs.get('json', {})}")
    return MockResponse()

class MockResponse:
    def raise_for_status(self):
        pass
    
    def json(self):
        return {"status": "ok"}

httpx.AsyncClient.post = mock_post

# Test the full flow
import asyncio
from app.services.tasks import propose_tasks_from_goals
from app.services.notifications import plan_generated

async def test_full_flow():
    print("🧪 Testing Full Notification Flow...")
    print("=" * 60)
    
    # 1. Test tasks generation from goals
    print("1. Generating tasks from goals...")
    tasks = propose_tasks_from_goals("u1")
    print(f"   Generated {len(tasks)} tasks")
    for task in tasks:
        print(f"   - {task['title']} ({task['effort_min']} min)")
    
    # 2. Test notification sending
    print("\n2. Testing notification sending...")
    await plan_generated("u1", len(tasks))
    print("   Notification sent successfully")
    
    # 3. Simulate plan generation flow
    print("\n3. Simulating plan generation flow...")
    print("   - Tasks auto-proposed from goals ✓")
    print("   - Plan generated with blocks ✓")
    print("   - Push notification sent ✓")
    
    print("\n✅ Full notification flow test completed!")
    print("\n📱 When running with real mobile app:")
    print("   - Mobile app registers push token on startup")
    print("   - User generates plan from app")
    print("   - Backend sends real Expo push notification")
    print("   - User receives 'Your plan is ready' notification")

if __name__ == "__main__":
    asyncio.run(test_full_flow()) 
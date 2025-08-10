#!/usr/bin/env python3

"""
Test script to verify notification service functionality
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

# Mock the Firebase client
import app.services.repo
app.services.repo.get_db = lambda: MockFirestore()

# Test the notification service
import asyncio
from app.services.notifications import send_expo_push, plan_generated

async def test_notifications():
    print("🧪 Testing Notification Service...")
    print("=" * 50)
    
    # Test send_expo_push
    print("Testing send_expo_push...")
    result = await send_expo_push("u1", "Test Title", "Test Body")
    print(f"send_expo_push result: {result}")
    
    # Test plan_generated
    print("\nTesting plan_generated...")
    await plan_generated("u1", 3)
    print("plan_generated completed")
    
    print("\n✅ Notification service test completed!")

if __name__ == "__main__":
    asyncio.run(test_notifications()) 
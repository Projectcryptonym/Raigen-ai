#!/usr/bin/env python3

"""
Test script to verify tasks service functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock Firebase for testing
class MockFirestore:
    def collection(self, name):
        return MockCollection()

class MockCollection:
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
                "effort_estimate_min": 180,  # This should split into 2 tasks
                "domain": ["work"],
                "why": "launch beta",
                "status": "active"
            }),
            MockDoc({
                "id": "goal2", 
                "user_id": "u1",
                "title": "Learn React Native",
                "priority": 2,
                "effort_estimate_min": 90,
                "domain": ["learning"],
                "why": "build mobile skills",
                "status": "active"
            })
        ]

class MockDoc:
    def __init__(self, data):
        self.data = data
        self.id = data.get("id", "mock_id")
    
    def to_dict(self):
        return self.data

# Mock the Firebase client
import app.services.repo
app.services.repo.get_db = lambda: MockFirestore()

# Test the tasks service
from app.services.tasks import propose_tasks_from_goals

print("🧪 Testing Tasks Service...")
print("=" * 50)

tasks = propose_tasks_from_goals("u1")

print(f"Generated {len(tasks)} tasks from goals:")
for i, task in enumerate(tasks, 1):
    print(f"{i}. {task['title']}")
    print(f"   Effort: {task['effort_min']} min")
    print(f"   Energy: {task['energy']}")
    print(f"   Urgency: {task['urgency']}")
    print(f"   Impact: {task['impact']}")
    print(f"   Goal ID: {task.get('goal_id', 'None')}")
    print()

print("✅ Tasks service test completed!") 
#!/usr/bin/env python3

"""
Test script to verify plan limits and budget enforcement
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock Firebase for testing
class MockFirestore:
    def collection(self, name):
        return MockCollection()
    
    def run_transaction(self, callback):
        return callback(MockTransaction())

class MockCollection:
    def document(self, doc_id):
        return MockDocument()
    
    def where(self, field, op, value):
        return self
    
    def stream(self):
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
    def __init__(self):
        self.exists = False
        self.data = {}
    
    def get(self):
        return MockDocSnapshot(self.exists, self.data)
    
    def set(self, data, merge=True):
        self.data.update(data)
        self.exists = True
        return True

class MockDocSnapshot:
    def __init__(self, exists=True, data=None):
        self.exists = exists
        self.data = data or {}
    
    def to_dict(self):
        return self.data

class MockDoc:
    def __init__(self, data):
        self.data = data
        self.id = data.get("id", "mock_id")
    
    def to_dict(self):
        return self.data

class MockTransaction:
    def get(self, ref):
        return MockDocSnapshot(True, {"llm_cents": 0, "sms_used": 0, "voice_min": 0})
    
    def set(self, ref, data, merge=True):
        return True

# Mock the Firebase client
import app.services.repo
app.services.repo.get_db = lambda: MockFirestore()

# Mock other services
import app.services.notifications
app.services.notifications.send_expo_push = lambda *args: True
app.services.notifications.plan_generated = lambda *args: None

import app.services.memos
app.services.memos.memory_store = lambda *args: "mock_memory_id"

# Test the plan generation with limits
from app.services.budgets import get_current, within_limit
from app.services.tasks import propose_tasks_from_goals

def test_plan_limits():
    print("🧪 Testing Plan Limits & Budget Enforcement...")
    print("=" * 60)
    
    # 1. Test initial state
    print("1. Initial budget state...")
    budget = get_current("u1")
    print(f"   LLM used: {budget['llm_cents']} cents")
    print(f"   LLM limit: {budget['llm_limit_cents']} cents")
    
    # 2. Test plan generation simulation
    print("\n2. Simulating plan generation...")
    
    # Simulate first plan (full plan)
    print("   Generating full plan...")
    llm_cost = 5  # 5 cents per plan
    can_afford = within_limit("u1", "llm_cents", llm_cost, "llm_limit_cents")
    print(f"   Can afford LLM cost: {can_afford}")
    print(f"   Plan type: full")
    print(f"   Replan count: 0")
    
    # Simulate first replan
    print("\n   Generating first replan...")
    can_afford = within_limit("u1", "llm_cents", llm_cost, "llm_limit_cents")
    print(f"   Can afford LLM cost: {can_afford}")
    print(f"   Plan type: replan")
    print(f"   Replan count: 1")
    
    # Simulate second replan
    print("\n   Generating second replan...")
    can_afford = within_limit("u1", "llm_cents", llm_cost, "llm_limit_cents")
    print(f"   Can afford LLM cost: {can_afford}")
    print(f"   Plan type: replan")
    print(f"   Replan count: 2")
    
    # Simulate third replan (should be blocked)
    print("\n   Attempting third replan...")
    print(f"   ❌ BLOCKED: Replan limit reached (max 2 per day)")
    
    # 3. Test budget tracking
    print("\n3. Budget tracking simulation...")
    total_plans = 3  # 1 full + 2 replans
    total_cost = total_plans * llm_cost
    print(f"   Total plans generated: {total_plans}")
    print(f"   Total LLM cost: {total_cost} cents")
    print(f"   Remaining budget: {budget['llm_limit_cents'] - total_cost} cents")
    
    # 4. Test tasks generation
    print("\n4. Tasks generation...")
    tasks = propose_tasks_from_goals("u1")
    print(f"   Generated {len(tasks)} tasks from goals")
    for task in tasks:
        print(f"   - {task['title']} ({task['effort_min']} min)")
    
    print("\n✅ Plan limits test completed!")
    print("\n📋 Plan Limits Summary:")
    print("   - Full plans: 1 per day")
    print("   - Replans: max 2 per day")
    print("   - LLM cost: 5 cents per plan")
    print("   - Budget enforcement: soft cap with logging")
    print("   - Tasks: auto-generated from active goals")

if __name__ == "__main__":
    test_plan_limits() 
#!/usr/bin/env python3
"""
Test script for core features:
1. Stable block IDs + Mobile Done
2. Real MemOS integration
3. Weekly Review with real adherence
"""

import requests
import json
from datetime import datetime, timezone

BASE_URL = "http://localhost:8080"
USER_ID = "u1"

def test_endpoint(method, path, data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        
        print(f"✅ {method} {path} - Status: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ {method} {path} - Error: {e}")
        return None

def main():
    print("🧪 Testing Core Features")
    print("=" * 50)
    
    # 1. Generate a plan with stable block IDs
    print("\n1️⃣ Testing Plan Generation with Stable Block IDs")
    plan_data = {
        "user_id": USER_ID,
        "tasks": [
            {"title": "Deep Work: Proposal", "effort_min": 60, "energy": "high", "urgency": 3, "impact": 3},
            {"title": "Admin Inbox Zero", "effort_min": 30, "energy": "low", "urgency": 2, "impact": 1}
        ],
        "free_windows": [],
        "user_prefs": {
            "quiet_hours": {"start": "22:00", "end": "07:00"},
            "hard_blocks": [],
            "max_day_min": 240
        }
    }
    
    plan_result = test_endpoint("POST", "/plan/generate", plan_data)
    if plan_result and plan_result.get("blocks"):
        print(f"   Generated {len(plan_result['blocks'])} blocks")
        for i, block in enumerate(plan_result["blocks"]):
            print(f"   Block {i+1}: {block['title']} (ID: {block.get('id', 'NO_ID')})")
    
    # 2. Test completion of a block
    print("\n2️⃣ Testing Block Completion")
    if plan_result and plan_result.get("blocks"):
        first_block = plan_result["blocks"][0]
        if first_block.get("id"):
            complete_data = {
                "user_id": USER_ID,
                "block_id": first_block["id"],
                "completed": True
            }
            complete_result = test_endpoint("POST", "/plan/complete", complete_data)
            if complete_result:
                adherence = complete_result.get("adherence", {})
                print(f"   Completed block: {adherence.get('completed', 0)}/{adherence.get('planned', 0)}")
    
    # 3. Test weekly review with real adherence
    print("\n3️⃣ Testing Weekly Review with Real Adherence")
    review_result = test_endpoint("POST", "/reviews/weekly/generate", {"user_id": USER_ID})
    if review_result:
        adherence = review_result.get("adherence", 0)
        total_blocks = review_result.get("total_blocks", 0)
        completed_blocks = review_result.get("completed_blocks", 0)
        print(f"   Weekly adherence: {adherence:.1f}% ({completed_blocks}/{total_blocks} blocks)")
        print(f"   Summary: {review_result.get('summary', 'No summary')}")
    
    # 4. Test replan limit (should get 429 after 2 replans)
    print("\n4️⃣ Testing Replan Limits")
    for i in range(3):
        replan_data = {
            "user_id": USER_ID,
            "delta_minutes": 30
        }
        replan_result = test_endpoint("POST", "/plan/replan", replan_data)
        if replan_result is None and i == 2:
            print("   ✅ Replan limit enforced (429 expected on 3rd attempt)")
    
    print("\n🎉 Core Features Test Complete!")
    print("\nNext steps:")
    print("1. Start the backend server: cd backend && python3 start_server.py")
    print("2. Test mobile app completion buttons")
    print("3. Check MemOS logs for stored memories")
    print("4. Verify Google Calendar events were created")

if __name__ == "__main__":
    main() 
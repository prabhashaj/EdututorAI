#!/usr/bin/env python3
"""
Test script to generate a quiz and check if it's properly logged in the history
"""

import requests
import json

# Base URL for the API
API_BASE = "http://localhost:8000/api"

def test_quiz_generation():
    """Test quiz generation and history tracking"""
    print("🧪 Testing Quiz Generation and History...")
    
    # Step 1: Generate a quiz
    print("\n📝 Step 1: Generating a quiz...")
    quiz_data = {
        "topic": "Python Programming",
        "difficulty": 3,
        "num_questions": 5
    }
    
    response = requests.post(f"{API_BASE}/quiz/generate", json=quiz_data)
    if response.status_code == 200:
        quiz = response.json()
        print(f"✅ Quiz generated successfully!")
        print(f"   Quiz ID: {quiz['id']}")
        print(f"   Topic: {quiz['topic']}")
        print(f"   Questions: {len(quiz['questions'])}")
        quiz_id = quiz['id']
    else:
        print(f"❌ Failed to generate quiz: {response.text}")
        return False
    
    # Step 2: Check educator history
    print("\n📚 Step 2: Checking educator quiz history...")
    response = requests.get(f"{API_BASE}/quiz/history/educator")
    if response.status_code == 200:
        history = response.json()
        print(f"✅ History retrieved successfully!")
        print(f"   Number of quizzes in history: {len(history['history'])}")
        
        if history['history']:
            latest_quiz = history['history'][0]
            print(f"   Latest quiz: {latest_quiz['topic']} (Status: {latest_quiz['status']})")
        else:
            print("   ⚠️ No quizzes found in history!")
            return False
    else:
        print(f"❌ Failed to get history: {response.text}")
        return False
    
    # Step 3: Test assignment (optional)
    print("\n🎯 Step 3: Testing quiz assignment...")
    assignment_data = {
        "quiz_id": quiz_id,
        "student_ids": ["student_alice", "student_bob"],
        "notification_message": "Test quiz assignment"
    }
    
    response = requests.post(f"{API_BASE}/quiz/assign", json=assignment_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Quiz assigned successfully!")
        print(f"   {result['message']}")
    else:
        print(f"❌ Failed to assign quiz: {response.text}")
        return False
    
    # Step 4: Check updated history
    print("\n📚 Step 4: Checking updated history after assignment...")
    response = requests.get(f"{API_BASE}/quiz/history/educator")
    if response.status_code == 200:
        history = response.json()
        if history['history']:
            latest_quiz = history['history'][0]
            print(f"✅ Updated history retrieved!")
            print(f"   Latest quiz status: {latest_quiz['status']}")
            print(f"   Students assigned: {latest_quiz.get('total_assigned', 0)}")
        else:
            print("   ⚠️ Still no quizzes in history!")
            return False
    else:
        print(f"❌ Failed to get updated history: {response.text}")
        return False
    
    print("\n🎉 All tests passed! Quiz generation and history tracking is working!")
    return True

if __name__ == "__main__":
    success = test_quiz_generation()
    if not success:
        print("\n❌ Some tests failed. Please check the backend logs.")
    else:
        print("\n✅ Quiz history should now be visible in the educator dashboard!")

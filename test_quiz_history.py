#!/usr/bin/env python3
"""
Test script to create quizzes and assignments to verify quiz history functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_quiz_generation_and_assignment():
    """Test quiz generation and assignment to populate history"""
    
    print("🚀 Testing Quiz Generation and Assignment")
    print("=" * 50)
    
    # Test 1: Generate a quiz
    print("\n📝 Step 1: Generating a test quiz...")
    quiz_data = {
        "topic": "Python Programming Basics",
        "difficulty": 3,
        "num_questions": 5
    }
    
    response = requests.post(f"{BASE_URL}/quiz/generate", json=quiz_data)
    if response.status_code == 200:
        quiz = response.json()
        quiz_id = quiz["id"]
        print(f"✅ Quiz generated successfully! ID: {quiz_id}")
        print(f"   Topic: {quiz['topic']}")
        print(f"   Questions: {len(quiz.get('questions', []))}")
    else:
        print(f"❌ Failed to generate quiz: {response.text}")
        return
    
    # Test 2: Assign the quiz to students
    print("\n👥 Step 2: Assigning quiz to students...")
    assignment_data = {
        "quiz_id": quiz_id,
        "student_ids": ["student_alice", "student_bob", "student_carol"],
        "notification_message": "Please complete this Python basics quiz by the end of the week."
    }
    
    response = requests.post(f"{BASE_URL}/quiz/assign", json=assignment_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Quiz assigned successfully!")
        print(f"   Assignment ID: {result.get('assignment_id')}")
        print(f"   Message: {result.get('message')}")
    else:
        print(f"❌ Failed to assign quiz: {response.text}")
        return
    
    # Test 3: Generate another quiz for variety
    print("\n📝 Step 3: Generating another test quiz...")
    quiz_data2 = {
        "topic": "Data Structures and Algorithms",
        "difficulty": 4,
        "num_questions": 7
    }
    
    response = requests.post(f"{BASE_URL}/quiz/generate", json=quiz_data2)
    if response.status_code == 200:
        quiz2 = response.json()
        quiz_id2 = quiz2["id"]
        print(f"✅ Second quiz generated successfully! ID: {quiz_id2}")
        print(f"   Topic: {quiz2['topic']}")
        print(f"   Questions: {len(quiz2.get('questions', []))}")
    else:
        print(f"❌ Failed to generate second quiz: {response.text}")
        return
    
    # Test 4: Check educator quiz history
    print("\n📚 Step 4: Checking educator quiz history...")
    response = requests.get(f"{BASE_URL}/quiz/history/educator")
    if response.status_code == 200:
        history = response.json().get("history", [])
        print(f"✅ Quiz history retrieved successfully!")
        print(f"   Total quizzes in history: {len(history)}")
        
        for i, quiz_info in enumerate(history, 1):
            print(f"\n   Quiz {i}:")
            print(f"     - Topic: {quiz_info['topic']}")
            print(f"     - Difficulty: {quiz_info['difficulty']}/5")
            print(f"     - Status: {quiz_info['status']}")
            print(f"     - Created: {quiz_info['created_at']}")
            if quiz_info['status'] == 'assigned':
                print(f"     - Assigned to: {quiz_info['total_assigned']} students")
    else:
        print(f"❌ Failed to get quiz history: {response.text}")
    
    # Test 5: Submit a quiz answer (simulate student taking quiz)
    print("\n🎯 Step 5: Simulating student quiz submission...")
    # Get the quiz with answers for testing
    response = requests.get(f"{BASE_URL}/quiz/{quiz_id}")
    if response.status_code == 200:
        quiz_for_student = response.json()
        
        # Simulate student answers (just pick first option for simplicity)
        student_answers = {}
        for i, question in enumerate(quiz_for_student.get('questions', [])):
            if question.get('options'):
                student_answers[str(i)] = question['options'][0]  # Always pick first option
        
        submission_data = {
            "quiz_id": quiz_id,
            "user_id": "student_alice",
            "answers": student_answers
        }
        
        response = requests.post(f"{BASE_URL}/quiz/submit", json=submission_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Quiz submission successful!")
            print(f"   Score: {result.get('score', 0):.1f}%")
            print(f"   Correct answers: {result.get('correct_answers', 0)}/{result.get('total_questions', 0)}")
        else:
            print(f"❌ Failed to submit quiz: {response.text}")
    
    # Test 6: Check updated history with completion data
    print("\n📈 Step 6: Checking updated quiz history with completion data...")
    time.sleep(1)  # Give a moment for data to update
    response = requests.get(f"{BASE_URL}/quiz/history/educator")
    if response.status_code == 200:
        history = response.json().get("history", [])
        print(f"✅ Updated quiz history retrieved!")
        
        for quiz_info in history:
            if quiz_info['quiz_id'] == quiz_id:
                print(f"\n   Updated stats for '{quiz_info['topic']}':")
                print(f"     - Completion rate: {quiz_info.get('completion_rate', 0):.1f}%")
                print(f"     - Completed: {quiz_info.get('completed_count', 0)}/{quiz_info.get('total_assigned', 0)} students")
                if quiz_info.get('completed_count', 0) > 0:
                    print(f"     - Average score: {quiz_info.get('average_score', 0):.1f}%")
    
    print("\n🎉 Quiz history test completed successfully!")
    print("You can now check the educator dashboard to see the quiz history in action.")

if __name__ == "__main__":
    try:
        test_quiz_generation_and_assignment()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

# frontend/app.py
import streamlit as st
import requests
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pages.login import render_login_page
from pages.student_dashboard import render_student_dashboard
from pages.educator_dashboard import render_educator_dashboard
from pages.quiz_interface import render_quiz_interface

# Configure page
st.set_page_config(
    page_title="EduTutor AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .quiz-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .score-display {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .success-score {
        background-color: #d4edda;
        color: #155724;
    }
    .warning-score {
        background-color: #fff3cd;
        color: #856404;
    }
    .danger-score {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}

def login_user(email: str, role: str, name: str = None):
    """Simulate user login"""
    user_id = f"{role}_{email.split('@')[0]}"
    st.session_state.user = {
        "id": user_id,
        "email": email,
        "role": role,
        "name": name or email.split('@')[0].title()
    }

def logout_user():
    """Logout user"""
    st.session_state.user = None
    st.session_state.current_quiz = None
    st.session_state.quiz_answers = {}

def generate_quiz(topic: str, difficulty: int, num_questions: int):
    """Generate quiz via API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/quiz/generate",
            json={
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": num_questions
            }
        )
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"Failed to generate quiz: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def submit_quiz(quiz_id: str, user_id: str, answers: dict):
    """Submit quiz answers via API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/quiz/submit",
            json={
                "quiz_id": quiz_id,
                "user_id": user_id,
                "answers": answers
            }
        )
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"Failed to submit quiz: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error submitting quiz: {str(e)}")
        return None

def get_quiz_history(user_id: str):
    """Get quiz history via API"""
    try:
        response = requests.get(f"{API_BASE_URL}/quiz/history/{user_id}")
        if response.status_code == 200:
            return response.json().get("history", [])
        else:
            return []
    except Exception as e:
        st.error(f"Error getting quiz history: {str(e)}")
        return []

def get_students_analytics():
    """Get students analytics via API"""
    try:
        response = requests.get(f"{API_BASE_URL}/quiz/analytics/students")
        if response.status_code == 200:
            return response.json().get("students", [])
        else:
            return []
    except Exception as e:
        st.error(f"Error getting analytics: {str(e)}")
        return []

def register_user(email: str, name: str, role: str, password: str):
    """Register a new user via API"""
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/register",
            json={
                "email": email,
                "name": name,
                "role": role,
                "password": password
            }
        )
        if response.status_code in [200, 201]:
            data = response.json()
            st.session_state.user = data.get("user")
            st.session_state.access_token = data.get("access_token")
            st.success("✅ Registration successful!")
            st.rerun()
        else:
            st.error("Registration failed: " + response.text)
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

def main():
    if 'user' not in st.session_state or st.session_state.user is None:
        render_login_page()
    else:
        role = st.session_state.user.get('role')
        if role == 'student':
            render_student_dashboard()
        elif role == 'educator':
            render_educator_dashboard()
        else:
            st.error('Unknown user role. Please log in again.')

if __name__ == "__main__":
    main()

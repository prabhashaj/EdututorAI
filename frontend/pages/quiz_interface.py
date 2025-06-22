# frontend/pages/quiz_interface.py
import streamlit as st
import time
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.quiz_generator import QuizGenerator

def render_quiz_interface():
    """Dedicated quiz interface page"""
    st.set_page_config(
        page_title="EduTutor AI - Quiz Interface",
        page_icon="📝",
        layout="wide"
    )
    
    # Custom CSS for quiz interface
    st.markdown("""
    <style>
        .quiz-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .question-card {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 1rem 0;
            border-left: 5px solid #667eea;
        }
        .option-button {
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .option-button:hover {
            background: #e9ecef;
            border-color: #667eea;
        }
        .selected-option {
            background: #667eea !important;
            color: white !important;
            border-color: #667eea !important;
        }
        .timer-display {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fff;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            z-index: 1000;
        }
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 10px;
            overflow: hidden;
        }
        .progress-fill {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            transition: width 0.3s ease;
        }
        .score-display {
            background: #d4edda;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            text-align: center;
        }
        .success-score {
            border-left: 5px solid #28a745;
        }
        .error-score {
            border-left: 5px solid #dc3545;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize quiz generator
    quiz_gen = QuizGenerator("http://localhost:8000/api")
    
    # Initialize session state
    if 'quiz_state' not in st.session_state:
        st.session_state.quiz_state = 'setup'  # setup, active, completed
    
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = {}
    
    if 'quiz_start_time' not in st.session_state:
        st.session_state.quiz_start_time = None
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    
    # Route based on quiz state
    if st.session_state.quiz_state == 'setup':
        render_quiz_setup(quiz_gen)
    elif st.session_state.quiz_state == 'active':
        render_active_quiz(quiz_gen)
    elif st.session_state.quiz_state == 'completed':
        render_quiz_results(quiz_gen)

def render_quiz_setup(quiz_gen):
    """Render quiz setup interface"""
    st.markdown("""
    <div class="quiz-header">
        <h1>📝 Quiz Setup</h1>
        <p>Configure your personalized quiz experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quiz configuration
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("quiz_setup_form"):
            st.markdown("### 🎯 Quiz Configuration")
            
            # Basic settings
            topic = st.text_input(
                "📚 Topic",
                placeholder="e.g., Python Programming, World History, Calculus",
                help="Enter the subject or topic you want to be quizzed on"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                difficulty = st.select_slider(
                    "⭐ Difficulty Level",
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    format_func=lambda x: {
                        1: "⭐ Beginner",
                        2: "⭐⭐ Easy", 
                        3: "⭐⭐⭐ Medium",
                        4: "⭐⭐⭐⭐ Hard",
                        5: "⭐⭐⭐⭐⭐ Expert"
                    }[x]
                )
            
            with col_b:
                num_questions = st.slider(
                    "📊 Number of Questions",
                    min_value=5,
                    max_value=20,
                    value=10,
                    help="Choose how many questions you want"
                )
            
            # Advanced settings
            with st.expander("🔧 Advanced Settings"):
                time_limit = st.selectbox(
                    "⏱️ Time Limit",
                    ["No Limit", "10 minutes", "15 minutes", "20 minutes", "30 minutes"]
                )
                
                question_type = st.selectbox(
                    "❓ Question Type",
                    ["Multiple Choice", "True/False", "Mixed"]
                )
                
                show_feedback = st.checkbox("💡 Show immediate feedback", value=True)
                randomize_questions = st.checkbox("🔀 Randomize question order", value=True)
            
            # Generate quiz button
            if st.form_submit_button("🚀 Generate Quiz", use_container_width=True, type="primary"):
                if topic:
                    generate_quiz_from_setup(quiz_gen, topic, difficulty, num_questions, time_limit)
                else:
                    st.error("⚠️ Please enter a topic for your quiz!")
    
    with col2:
        # Quick start templates
        st.markdown("### ⚡ Quick Start Templates")
        
        templates = [
            {"name": "🐍 Python Basics", "topic": "Python Programming", "difficulty": 2, "questions": 10},
            {"name": "📊 Data Science", "topic": "Data Science", "difficulty": 3, "questions": 8},
            {"name": "🌍 World Geography", "topic": "Geography", "difficulty": 2, "questions": 12},
            {"name": "🧮 Basic Math", "topic": "Mathematics", "difficulty": 2, "questions": 15},
            {"name": "📚 English Grammar", "topic": "English Grammar", "difficulty": 2, "questions": 10},
        ]
        
        for template in templates:
            if st.button(template["name"], use_container_width=True, key=f"template_{template['name']}"):
                generate_quiz_from_setup(
                    quiz_gen, 
                    template["topic"], 
                    template["difficulty"], 
                    template["questions"],
                    "15 minutes"
                )

def generate_quiz_from_setup(quiz_gen, topic, difficulty, num_questions, time_limit):
    """Generate quiz from setup parameters"""
    with st.spinner("🤖 Generating your personalized quiz..."):
        quiz = quiz_gen.generate_quiz(topic, difficulty, num_questions)
        
        if quiz:
            st.session_state.current_quiz = quiz
            st.session_state.quiz_answers = {}
            st.session_state.quiz_start_time = datetime.now()
            st.session_state.current_question = 0
            st.session_state.quiz_state = 'active'
            st.session_state.time_limit = time_limit
            
            st.success("✅ Quiz generated successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Failed to generate quiz. Please try again.")

def render_active_quiz(quiz_gen):
    """Render active quiz interface"""
    quiz = st.session_state.current_quiz
    current_q = st.session_state.current_question
    total_questions = len(quiz['questions'])
    
    # Quiz header with progress
    progress = (current_q + 1) / total_questions
    st.markdown(f"""
    <div class="quiz-header">
        <h2>📝 {quiz['title']}</h2>
        <p>Question {current_q + 1} of {total_questions}</p>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress * 100}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Timer (if applicable)
    if st.session_state.get('time_limit') != "No Limit":
        render_timer(quiz_gen)
    
    # Current question
    question = quiz['questions'][current_q]
    
    st.markdown(f"""
    <div class="question-card">
        <h3>Question {current_q + 1}</h3>
        <h4>{question['question']}</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Answer options
    selected_answer = st.radio(
        "Choose your answer:",
        question['options'],
        key=f"question_{current_q}",
        index=None if current_q not in st.session_state.quiz_answers else question['options'].index(st.session_state.quiz_answers[current_q])
    )
    
    if selected_answer:
        st.session_state.quiz_answers[current_q] = selected_answer
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if current_q > 0:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.current_question -= 1
                st.rerun()
    
    with col2:
        # Show progress
        answered = len(st.session_state.quiz_answers)
        st.write(f"📊 Progress: {answered}/{total_questions}")
    
    with col3:
        if current_q < total_questions - 1:
            if st.button("Next ➡️", use_container_width=True, disabled=selected_answer is None):
                st.session_state.current_question += 1
                st.rerun()
    
    with col4:
        if current_q == total_questions - 1:
            if st.button("🏁 Finish Quiz", use_container_width=True, type="primary", disabled=len(st.session_state.quiz_answers) != total_questions):
                submit_quiz(quiz_gen)
        else:
            # Show submit option if all questions answered
            if len(st.session_state.quiz_answers) == total_questions:
                if st.button("🏁 Submit Early", use_container_width=True, type="secondary"):
                    submit_quiz(quiz_gen)
    
    # Question overview
    with st.expander("📋 Question Overview"):
        cols = st.columns(min(5, total_questions))
        for i in range(total_questions):
            with cols[i % 5]:
                status = "✅" if i in st.session_state.quiz_answers else "⭕"
                color = "green" if i in st.session_state.quiz_answers else "gray"
                if st.button(f"{status} Q{i+1}", key=f"nav_q_{i}", help=f"Go to question {i+1}"):
                    st.session_state.current_question = i
                    st.rerun()

def render_timer(quiz_gen=None):
    """Render quiz timer"""
    if st.session_state.quiz_start_time and st.session_state.get('time_limit') != "No Limit":
        time_limit_minutes = int(st.session_state.time_limit.split()[0])
        elapsed = datetime.now() - st.session_state.quiz_start_time
        remaining = (time_limit_minutes * 60) - elapsed.total_seconds()
        if remaining > 0:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            # Color coding for urgency
            if remaining < 60:  # Less than 1 minute
                color = "#dc3545"
            elif remaining < 300:  # Less than 5 minutes
                color = "#ffc107"
            else:
                color = "#28a745"
            st.markdown(f"""
            <div class="timer-display" style="border-left: 4px solid {color};">
                <h4 style="margin: 0; color: {color};">⏱️ Time Remaining</h4>
                <h2 style="margin: 0; color: {color};">{minutes:02d}:{seconds:02d}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Time's up!
            st.error("⏰ Time's up! Submitting quiz automatically...")
            if quiz_gen is not None:
                submit_quiz(quiz_gen)

def submit_quiz(quiz_gen):
    """Submit the quiz"""
    user_id = None
    if 'user' in st.session_state and 'id' in st.session_state.user:
        user_id = st.session_state.user['id']
    else:
        st.error("User not logged in. Please login to submit the quiz.")
        return
    with st.spinner("📊 Submitting your quiz..."):
        result = quiz_gen.submit_quiz(
            st.session_state.current_quiz['id'],
            user_id,
            st.session_state.quiz_answers
        )
        if result:
            st.session_state.quiz_state = 'completed'
            st.session_state.quiz_results = result
            st.success("✅ Quiz submitted successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Failed to submit quiz. Please try again.")

def render_quiz_results(quiz_gen):
    """Render quiz results after submission"""
    if 'quiz_results' not in st.session_state or not st.session_state.quiz_results:
        st.error("No quiz results to display.")
        return
    results = st.session_state.quiz_results
    quiz = st.session_state.current_quiz

    st.markdown("""
    <div class="quiz-header">
        <h1>🏆 Quiz Results</h1>
        <p>See your performance and feedback below</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="score-display success-score">
        <h2>Score: {results.get('score', 0)} / {results.get('total_questions', len(quiz['questions']))}</h2>
        <p>Correct Answers: {results.get('correct_answers', 0)}</p>
    </div>
    """, unsafe_allow_html=True)

    # Feedback section
    if 'feedback' in results and results['feedback']:
        st.markdown("### 💡 Feedback & Explanations")
        for idx, feedback in enumerate(results['feedback']):
            st.markdown(f"**Q{idx+1}:** {feedback}")

    # Option to retake or go back
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Retake Quiz", use_container_width=True):
            st.session_state.quiz_state = 'setup'
            st.session_state.current_quiz = None
            st.session_state.quiz_answers = {}
            st.session_state.quiz_results = None
            st.session_state.quiz_start_time = None
            st.session_state.current_question = 0
            st.rerun()
    with col2:
        if st.button("🏠 Back to Dashboard", use_container_width=True):
            st.session_state.quiz_state = 'setup'
            st.session_state.current_quiz = None
            st.session_state.quiz_answers = {}
            st.session_state.quiz_results = None
            st.session_state.quiz_start_time = None
            st.session_state.current_question = 0
            st.rerun()

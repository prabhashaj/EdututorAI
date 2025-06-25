# frontend/pages/student_dashboard.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.quiz_generator import QuizGenerator
from components.analytics import AnalyticsComponent

def render_student_dashboard():
    """Main student dashboard"""
    if 'user' not in st.session_state or st.session_state.user['role'] != 'student':
        st.error("Access denied. Please login as a student.")
        return
    
    user = st.session_state.user
    
    # Initialize page selection but don't set default yet
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "📝 Take Quiz"
    
    # Page config
    st.set_page_config(
        page_title=f"EduTutor AI - {user['name']}",
        page_icon="👨‍🎓",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .quiz-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>👨‍🎓 Welcome back, {user['name']}!</h1>
        <p>Ready to learn something new today?</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        current_page = st.radio(
            "Go to:",
            ["📝 Take Quiz", "📚 Quiz History"],
            key="nav_radio",
            index=0 if st.session_state.current_page == "📝 Take Quiz" else 1
        )
        
        # Update the current page after the widget is rendered
        st.session_state.current_page = current_page
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
    
    # Route to different pages
    if st.session_state.current_page == "📝 Take Quiz":
        render_quiz_section()
    elif st.session_state.current_page == "📚 Quiz History":
        render_history_section()

def render_student_home():
    """Render student home dashboard"""
    st.markdown("## 📊 Your Learning Dashboard")
    
    # Initialize components
    analytics = AnalyticsComponent("http://localhost:8000/api")
    quiz_gen = QuizGenerator("http://localhost:8000/api")
    
    # Get user data
    user_id = st.session_state.user['id']
    
    # Get assigned quizzes
    try:
        response = requests.get(f"http://localhost:8000/api/quiz/assignments/{user_id}")
        if response.status_code == 200:
            assignments = response.json().get("assignments", [])
            
            if assignments:
                st.markdown("### 📬 New Assigned Quizzes")
                for assignment in assignments:
                    if not assignment.get("completed", False):
                        with st.expander(f"📝 {assignment['quiz_title']} - {assignment['quiz_topic']}"):
                            st.markdown(f"**Topic:** {assignment['quiz_topic']}")
                            st.markdown(f"**Assigned:** {assignment['assigned_at']}")
                            
                            if assignment.get("notification_message"):
                                st.info(assignment["notification_message"])
                                
                            if st.button("Take Quiz", key=f"take_{assignment['quiz_id']}"):
                                st.session_state.current_quiz_id = assignment['quiz_id']
                                st.rerun()
        else:
            st.error("Failed to fetch assigned quizzes")
    except Exception as e:
        st.error(f"Error fetching assignments: {e}")
    
    # Get quiz history
    history = analytics.get_quiz_history(user_id)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    total_quizzes = len(history)
    avg_score = sum([q['score'] for q in history]) / total_quizzes if total_quizzes > 0 else 0
    recent_quiz = history[0] if history else None
    streak = calculate_learning_streak(history)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📚 Total Quizzes</h3>
            <h2>{}</h2>
        </div>
        """.format(total_quizzes), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Average Score</h3>
            <h2>{:.1f}%</h2>
        </div>
        """.format(avg_score), unsafe_allow_html=True)
    
    with col3:
        last_score = recent_quiz['score'] if recent_quiz else 0
        st.markdown("""
        <div class="metric-card">
            <h3>🎯 Last Score</h3>
            <h2>{:.1f}%</h2>
        </div>
        """.format(last_score), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>🔥 Learning Streak</h3>
            <h2>{} days</h2>
        </div>
        """.format(streak), unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Take New Quiz", use_container_width=True, type="primary"):
            st.session_state.current_page = "📝 Take Quiz"
            st.experimental_rerun()
            return
    
    with col2:
        if st.button("📊 View Your Quiz Results", use_container_width=True):
            st.session_state.current_page = "� Quiz History"
            st.experimental_rerun()
            return
    
    with col3:
        if st.button("📚 Quiz History", use_container_width=True):
            st.session_state.current_page = "📚 Quiz History"
            st.experimental_rerun()
            return
    
    # Recent activity
    if history:
        st.markdown("### 📈 Recent Performance")
        
        # Performance chart
        if len(history) >= 3:
            df = pd.DataFrame(history[:10])  # Last 10 quizzes
            df['submitted_at'] = pd.to_datetime(df['submitted_at'])
            df = df.sort_values('submitted_at')
            
            fig = px.line(
                df, 
                x='submitted_at', 
                y='score',
                title='Recent Quiz Scores',
                markers=True,
                line_shape='spline'
            )
            fig.update_traces(line_color='#667eea', line_width=3, marker_size=8)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent quizzes
        st.markdown("### 📚 Recent Quizzes")
        for i, quiz in enumerate(history[:5]):
            score_color = get_score_color(quiz['score'])
            st.markdown(f"""
            <div class="quiz-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4>{quiz['topic']}</h4>
                        <p>Difficulty: {'⭐' * quiz['difficulty']} | Date: {quiz['submitted_at'][:10]}</p>
                    </div>
                    <div style="text-align: right;">
                        <h3 style="color: {score_color};">{quiz['score']:.1f}%</h3>
                        <p>{quiz['correct_answers']}/{quiz['total_questions']} correct</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.info("🌟 Welcome to EduTutor AI! Take your first quiz to start your learning journey.")
        if st.button("🚀 Start Your First Quiz", use_container_width=True, type="primary"):
            st.session_state.current_page = "📝 Take Quiz"
            st.experimental_rerun()
            return

def render_quiz_section():
    """Render quiz taking section"""
    st.markdown("## 📝 Take a Quiz")
    
    quiz_gen = QuizGenerator("http://localhost:8000/api")
    user_id = st.session_state.user['id']
    
    # Check if there's an active quiz
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    
    # Get assigned quizzes
    has_assigned_quizzes = False
    try:
        response = requests.get(f"http://localhost:8000/api/quiz/assignments/{user_id}")
        if response.status_code == 200:
            assignments = response.json().get("assignments", [])
            
            if assignments:
                has_assigned_quizzes = True
                st.markdown("### 📬 Available Quizzes")
                for assignment in assignments:
                    if not assignment.get("completed", False):
                        with st.expander(f"📝 {assignment['quiz_title']} - {assignment['quiz_topic']}"):
                            st.markdown(f"**Topic:** {assignment['quiz_topic']}")
                            st.markdown(f"**Assigned:** {assignment['assigned_at']}")
                            
                            if assignment.get("notification_message"):
                                st.info(assignment["notification_message"])
                                
                            if st.button("Start Quiz", key=f"start_{assignment['quiz_id']}"):
                                # Get the quiz details
                                with st.spinner("Loading quiz..."):
                                    try:
                                        quiz_response = requests.get(f"http://localhost:8000/api/quiz/{assignment['quiz_id']}")
                                        if quiz_response.status_code == 200:
                                            quiz = quiz_response.json()
                                            st.session_state.current_quiz = quiz
                                            st.success("✅ Quiz loaded successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to load quiz: {quiz_response.text}")
                                    except Exception as e:
                                        st.error(f"Error loading quiz: {str(e)}")
                                        
    except Exception as e:
        st.error(f"Error fetching assignments: {e}")
        return

    # If no assigned quizzes and no active quiz
    if not has_assigned_quizzes and st.session_state.current_quiz is None:
        st.info("📝 No quizzes have been assigned yet. Please wait for your educator to assign quizzes.")
        return
    
    # Display active quiz interface
    if st.session_state.current_quiz:
        quiz = st.session_state.current_quiz
        
        # Add a back button to return to quiz list
        if st.button("← Back to Quiz List"):
            st.session_state.current_quiz = None
            st.rerun()
            return
        
        # Render quiz interface and handle submission
        answers = quiz_gen.render_quiz_interface(quiz)
        
        if answers:
            with st.spinner("📊 Evaluating your answers..."):
                result = quiz_gen.submit_quiz(
                    quiz['id'],
                    st.session_state.user['id'],
                    answers
                )
                
                if result:
                    st.session_state.quiz_result = result
                    st.session_state.current_quiz = None
                    st.rerun()
    
    # Display quiz result
    if 'quiz_result' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 Quiz Results")
        
        result = st.session_state.quiz_result
        score = result.get('score', 0)
        correct = result.get('correct_answers', 0)
        total = result.get('total_questions', 0)
        
        # Display score with appropriate color
        score_color = get_score_color(score)
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background-color: {score_color}25; border-radius: 10px; margin: 1rem 0;">
            <h1 style="color: {score_color};">{score:.1f}%</h1>
            <p>You got {correct} out of {total} questions correct!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display feedback if available
        if 'feedback' in result:
            st.markdown("### 📝 Detailed Feedback")
            for i, feedback in enumerate(result['feedback']):
                with st.expander(f"Question {i+1}"):
                    st.markdown(feedback)
        
        # Show that this quiz is now part of their history
        st.success("✅ This quiz has been added to your quiz history!")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Take Another Quiz", use_container_width=True, type="primary"):
                del st.session_state.quiz_result
                st.rerun()
        
        with col2:
            if st.button("📊 View Quiz History", use_container_width=True):
                del st.session_state.quiz_result
                st.session_state.current_page = "📚 Quiz History"
                st.rerun()

# Progress section removed as we simplified the navigation

def render_history_section():
    """Render quiz history section"""
    st.markdown("## 📚 Quiz History")
    
    # Add refresh button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    analytics = AnalyticsComponent("http://localhost:8000/api")
    history = analytics.get_quiz_history(st.session_state.user['id'])
    
    if history:
        st.markdown("### Your Completed Quizzes")
        st.info(f"📊 You have completed {len(history)} quiz(s) so far!")
        
        # Create a nice table of all quizzes
        quiz_data = []
        for quiz in history:
            quiz_data.append({
                "Topic": quiz['topic'],
                "Date": quiz['submitted_at'][:10],
                "Score": f"{quiz['score']:.1f}%",
                "Correct": f"{quiz['correct_answers']}/{quiz['total_questions']}",
                "Difficulty": "⭐" * quiz['difficulty']
            })
        
        if quiz_data:
            df = pd.DataFrame(quiz_data)
            st.dataframe(df, use_container_width=True)
        
        # Display detailed history
        st.markdown("### Detailed Results")
        for i, quiz in enumerate(history):
            with st.expander(f"Quiz {i+1}: {quiz['topic']} - {quiz['submitted_at'][:10]}"):
                # Create score display
                score_color = "#28a745" if quiz['score'] >= 80 else "#ffc107" if quiz['score'] >= 60 else "#dc3545"
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background-color: {score_color}25; 
                            border-radius: 10px; margin-bottom: 1rem;">
                    <h1 style="color: {score_color};">{quiz['score']:.1f}%</h1>
                    <p>Score: {quiz['correct_answers']} correct out of {quiz['total_questions']} questions</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show feedback if available
                if 'feedback' in quiz:
                    st.markdown("#### Question Feedback")
                    for feedback_item in quiz['feedback']:
                        st.markdown(f"- {feedback_item}")
    
    else:
        st.info("📚 No quiz history found. Take some quizzes to build your learning history!")
        if st.button("🚀 Take Your First Quiz", use_container_width=True, type="primary"):
            st.session_state.current_page = "📝 Take Quiz"
            st.rerun()

# Settings section removed as we simplified the navigation

def calculate_learning_streak(history):
    """Calculate learning streak in days"""
    if not history:
        return 0
    
    # Sort by date
    dates = sorted([pd.to_datetime(q['submitted_at']).date() for q in history], reverse=True)
    
    streak = 0
    current_date = datetime.now().date()
    
    for date in dates:
        if (current_date - date).days <= streak + 1:
            streak += 1
            current_date = date
        else:
            break
    
    return streak

def get_score_color(score):
    """Get color based on score"""
    if score >= 90:
        return "#28a745"  # Green
    elif score >= 70:
        return "#ffc107"  # Yellow
    elif score >= 50:
        return "#fd7e14"  # Orange
    else:
        return "#dc3545"  # Red

def apply_filters(history, topic, difficulty, date_range):
    """Apply filters to quiz history"""
    filtered = history.copy()
    
    # Topic filter
    if topic != "All Topics":
        filtered = [q for q in filtered if q['topic'] == topic]
    
    # Difficulty filter
    if difficulty != "All Levels":
        filtered = [q for q in filtered if q['difficulty'] == difficulty]
    
    # Date filter
    if date_range != "All Time":
        days_map = {
            "Last 7 days": 7,
            "Last 30 days": 30,
            "Last 90 days": 90
        }
        days = days_map[date_range]
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered = [q for q in filtered if pd.to_datetime(q['submitted_at']) >= cutoff_date]
    
    return filtered

def logout_user():
    """Logout user and clear session"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

if __name__ == "__main__":
    render_student_dashboard()

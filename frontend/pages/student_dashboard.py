# frontend/pages/student_dashboard.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
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
        page = st.radio(
            "Go to:",
            ["🏠 Dashboard", "📝 Take Quiz", "📊 My Progress", "📚 Quiz History", "⚙️ Settings"],
            key="student_nav"
        )
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
    
    # Route to different pages
    if page == "🏠 Dashboard":
        render_student_home()
    elif page == "📝 Take Quiz":
        render_quiz_section()
    elif page == "📊 My Progress":
        render_progress_section()
    elif page == "📚 Quiz History":
        render_history_section()
    elif page == "⚙️ Settings":
        render_settings_section()

def render_student_home():
    """Render student home dashboard"""
    st.markdown("## 📊 Your Learning Dashboard")
    
    # Initialize components
    analytics = AnalyticsComponent("http://localhost:8000/api")
    quiz_gen = QuizGenerator("http://localhost:8000/api")
    
    # Get user data
    user_id = st.session_state.user['id']
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
            st.session_state.student_nav = "📝 Take Quiz"
            st.experimental_rerun()
            return
    
    with col2:
        if st.button("📊 View Progress", use_container_width=True):
            st.session_state.student_nav = "📊 My Progress"
            st.experimental_rerun()
            return
    
    with col3:
        if st.button("📚 Quiz History", use_container_width=True):
            st.session_state.student_nav = "📚 Quiz History"
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
            st.session_state.student_nav = "📝 Take Quiz"
            st.experimental_rerun()
            return

def render_quiz_section():
    """Render quiz taking section"""
    st.markdown("## 📝 Take a Quiz")
    
    quiz_gen = QuizGenerator("http://localhost:8000/api")
    
    # Check if there's an active quiz
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = {}
    
    if st.session_state.current_quiz is None:
        # Quiz generation interface
        quiz_params = quiz_gen.render_quiz_form()
        
        if quiz_params:
            with st.spinner("🤖 Generating your personalized quiz..."):
                quiz = quiz_gen.generate_quiz(
                    quiz_params['topic'],
                    quiz_params['difficulty'],
                    quiz_params['num_questions']
                )
                
                if quiz:
                    st.session_state.current_quiz = quiz
                    st.session_state.quiz_answers = {}
                    st.success("✅ Quiz generated successfully!")
                    st.rerun()
    
    else:
        # Quiz interface
        quiz = st.session_state.current_quiz
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
                    st.session_state.quiz_answers = {}
                    st.rerun()
    
    # Display quiz result
    if 'quiz_result' in st.session_state:
        quiz_gen.render_quiz_result(st.session_state.quiz_result)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Take Another Quiz", use_container_width=True, type="primary"):
                del st.session_state.quiz_result
                st.rerun()
        
        with col2:
            if st.button("📊 View Progress", use_container_width=True):
                del st.session_state.quiz_result
                st.session_state.student_nav = "📊 My Progress"
                st.rerun()

def render_progress_section():
    """Render progress analytics section"""
    st.markdown("## 📊 Your Learning Progress")
    
    analytics = AnalyticsComponent("http://localhost:8000/api")
    analytics.render_student_analytics(st.session_state.user['id'])

def render_history_section():
    """Render quiz history section"""
    st.markdown("## 📚 Quiz History")
    
    analytics = AnalyticsComponent("http://localhost:8000/api")
    history = analytics.get_quiz_history(st.session_state.user['id'])
    
    if history:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            topics = list(set([q['topic'] for q in history]))
            selected_topic = st.selectbox("Filter by Topic", ["All Topics"] + topics)
        
        with col2:
            difficulties = list(set([q['difficulty'] for q in history]))
            selected_difficulty = st.selectbox("Filter by Difficulty", ["All Levels"] + sorted(difficulties))
        
        with col3:
            date_range = st.selectbox("Date Range", ["All Time", "Last 7 days", "Last 30 days", "Last 90 days"])
        
        # Apply filters
        filtered_history = apply_filters(history, selected_topic, selected_difficulty, date_range)
        
        # Display filtered history
        for quiz in filtered_history:
            score_color = get_score_color(quiz['score'])
            difficulty_stars = '⭐' * quiz['difficulty']
            
            with st.expander(f"{quiz['topic']} - {quiz['score']:.1f}% ({quiz['submitted_at'][:10]})"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Score", f"{quiz['score']:.1f}%")
                with col2:
                    st.metric("Correct", f"{quiz['correct_answers']}/{quiz['total_questions']}")
                with col3:
                    st.metric("Difficulty", difficulty_stars)
                with col4:
                    st.metric("Date", quiz['submitted_at'][:10])
    
    else:
        st.info("📚 No quiz history found. Take some quizzes to build your learning history!")

def render_settings_section():
    """Render settings section"""
    st.markdown("## ⚙️ Settings")
    
    user = st.session_state.user
    
    # Profile settings
    st.markdown("### 👤 Profile Settings")
    with st.form("profile_form"):
        name = st.text_input("Name", value=user.get('name', ''))
        email = st.text_input("Email", value=user.get('email', ''), disabled=True)
        
        if st.form_submit_button("💾 Save Changes"):
            st.session_state.user['name'] = name
            st.success("✅ Profile updated successfully!")
    
    # Learning preferences
    st.markdown("### 🎯 Learning Preferences")
    with st.form("preferences_form"):
        preferred_difficulty = st.slider("Preferred Difficulty Level", 1, 5, 3)
        preferred_topics = st.multiselect(
            "Favorite Topics",
            ["Mathematics", "Science", "History", "Literature", "Programming", "Languages"],
            default=["Mathematics", "Science"]
        )
        quiz_length = st.selectbox("Preferred Quiz Length", [5, 10, 15, 20])
        
        if st.form_submit_button("💾 Save Preferences"):
            st.success("✅ Preferences saved successfully!")
    
    # Data export
    st.markdown("### 📊 Data Export")
    if st.button("📥 Export Quiz History", use_container_width=True):
        analytics = AnalyticsComponent("http://localhost:8000/api")
        history = analytics.get_quiz_history(st.session_state.user['id'])
        
        if history:
            df = pd.DataFrame(history)
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"quiz_history_{user['name'].replace(' ', '_')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data to export")

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

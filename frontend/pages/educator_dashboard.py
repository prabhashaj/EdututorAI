# frontend/pages/educator_dashboard.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.analytics import AnalyticsComponent
from components.quiz_generator import QuizGenerator

def render_educator_dashboard():
    """Main educator dashboard"""
    if 'user' not in st.session_state or st.session_state.user['role'] != 'educator':
        st.error("Access denied. Please login as an educator.")
        return
    
    user = st.session_state.user
    
    # Page config
    st.set_page_config(
        page_title=f"EduTutor AI - {user['name']} (Educator)",
        page_icon="👨‍🏫",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .educator-header {
            background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .student-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 0.5rem 0;
            border-left: 4px solid #11998e;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #dee2e6;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
    <div class="educator-header">
        <h1>👨‍🏫 Educator Dashboard - {user['name']}</h1>
        <p>Monitor student progress and manage learning activities</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        page = st.radio(
            "Go to:",
            ["📊 Class Analytics", "👥 Student Progress", "📝 Quiz Management", "📚 Content Library", "⚙️ Settings"],
            key="educator_nav"
        )
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
    
    # Route to different pages
    if page == "📊 Class Analytics":
        render_class_analytics()
    elif page == "👥 Student Progress":
        render_student_management()
    elif page == "📝 Quiz Management":
        render_quiz_management()
    elif page == "📚 Content Library":
        render_content_library()
    elif page == "⚙️ Settings":
        render_educator_settings()

def render_class_analytics():
    """Render class analytics overview"""
    st.markdown("## 📊 Class Analytics Overview")
    
    analytics = AnalyticsComponent("http://localhost:8000/api")
    students_data = analytics.get_students_analytics()
    
    if not students_data:
        st.info("👥 No student data available yet. Students need to take quizzes to generate analytics.")
        return
    
    # Overall class metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_students = len(students_data)
    active_students = len([s for s in students_data if s['total_quizzes'] > 0])
    total_quizzes = sum([s['total_quizzes'] for s in students_data])
    class_avg = sum([s['average_score'] for s in students_data if s['total_quizzes'] > 0]) / active_students if active_students > 0 else 0
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>👥 Total Students</h3>
            <h2 style="color: #11998e;">{}</h2>
        </div>
        """.format(total_students), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>🎯 Active Students</h3>
            <h2 style="color: #38ef7d;">{}</h2>
        </div>
        """.format(active_students), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📝 Total Quizzes</h3>
            <h2 style="color: #667eea;">{}</h2>
        </div>
        """.format(total_quizzes), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Class Average</h3>
            <h2 style="color: #764ba2;">{:.1f}%</h2>
        </div>
        """.format(class_avg), unsafe_allow_html=True)
    
    # Performance distribution
    if active_students > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Score Distribution")
            scores = [s['average_score'] for s in students_data if s['total_quizzes'] > 0]
            
            fig = px.histogram(
                scores,
                nbins=10,
                title='Distribution of Student Average Scores',
                labels={'value': 'Average Score (%)', 'count': 'Number of Students'},
                color_discrete_sequence=['#11998e']
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🎯 Performance Categories")
            
            # Categorize students
            excellent = len([s for s in students_data if s['total_quizzes'] > 0 and s['average_score'] >= 90])
            good = len([s for s in students_data if s['total_quizzes'] > 0 and 70 <= s['average_score'] < 90])
            average = len([s for s in students_data if s['total_quizzes'] > 0 and 50 <= s['average_score'] < 70])
            needs_help = len([s for s in students_data if s['total_quizzes'] > 0 and s['average_score'] < 50])
            
            categories = ['Excellent (90%+)', 'Good (70-89%)', 'Average (50-69%)', 'Needs Help (<50%)']
            values = [excellent, good, average, needs_help]
            colors = ['#28a745', '#38ef7d', '#ffc107', '#dc3545']
            
            fig = px.pie(
                values=values,
                names=categories,
                title='Student Performance Categories',
                color_discrete_sequence=colors
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Top performers
    st.markdown("### 🏆 Top Performers")
    top_students = sorted(
        [s for s in students_data if s['total_quizzes'] > 0],
        key=lambda x: x['average_score'],
        reverse=True
    )[:10]
    
    if top_students:
        for i, student in enumerate(top_students):
            st.markdown(f"""
            <div class="student-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4>#{i+1} {student['name']}</h4>
                        <p>{student['email']} | {student['total_quizzes']} quizzes completed</p>
                    </div>
                    <div style="text-align: right;">
                        <h3 style="color: #11998e;">{student['average_score']:.1f}%</h3>
                        <p>Last activity: {student['quiz_history'][0]['submitted_at'][:10] if student['quiz_history'] else 'N/A'}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Recent activity timeline
    st.markdown("### 📅 Recent Activity")
    all_quizzes = []
    for student in students_data:
        for quiz in student['quiz_history'][:5]:  # Last 5 quizzes per student
            quiz['student_name'] = student['name']
            all_quizzes.append(quiz)
    
    if all_quizzes:
        # Sort by date
        all_quizzes.sort(key=lambda x: x['submitted_at'], reverse=True)
        
        for quiz in all_quizzes[:10]:  # Show last 10 activities
            score_color = get_score_color(quiz['score'])
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 0.5rem; margin: 0.25rem 0; border-radius: 5px; border-left: 3px solid {score_color};">
                <strong>{quiz['student_name']}</strong> completed <strong>{quiz['topic']}</strong> 
                - Score: <span style="color: {score_color}; font-weight: bold;">{quiz['score']:.1f}%</span>
                <small style="float: right; color: #666;">{quiz['submitted_at'][:16]}</small>
            </div>
            """, unsafe_allow_html=True)

def render_student_management():
    """Render individual student progress management"""
    st.markdown("## 👥 Student Progress Management")
    
    analytics = AnalyticsComponent("http://localhost:8000/api")
    students_data = analytics.get_students_analytics()
    
    if not students_data:
        st.info("👥 No student data available.")
        return
    
    # Student selector
    student_options = [f"{s['name']} ({s['email']})" for s in students_data]
    selected_idx = st.selectbox("Select Student", range(len(student_options)), format_func=lambda x: student_options[x])
    
    if selected_idx is not None:
        student = students_data[selected_idx]
        
        # Student overview
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### 📋 {student['name']}'s Profile")
            st.write(f"**Email:** {student['email']}")
            st.write(f"**Total Quizzes:** {student['total_quizzes']}")
            st.write(f"**Average Score:** {student['average_score']:.1f}%")
            
            if student['quiz_history']:
                latest_quiz = student['quiz_history'][0]
                st.write(f"**Last Activity:** {latest_quiz['submitted_at'][:10]}")
                st.write(f"**Last Score:** {latest_quiz['score']:.1f}%")
        
        with col2:
            # Performance indicator
            avg_score = student['average_score']
            if avg_score >= 90:
                status = "🟢 Excellent"
                color = "#28a745"
            elif avg_score >= 70:
                status = "🟡 Good"
                color = "#ffc107"
            elif avg_score >= 50:
                status = "🟠 Average"
                color = "#fd7e14"
            else:
                status = "🔴 Needs Help"
                color = "#dc3545"
            
            st.markdown(f"""
            <div style="background: {color}20; border: 2px solid {color}; padding: 1rem; border-radius: 8px; text-align: center;">
                <h3 style="color: {color}; margin: 0;">{status}</h3>
                <p style="margin: 0;">Performance Level</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed analytics for selected student
        if student['quiz_history']:
            # Performance over time
            st.markdown("### 📈 Performance Trend")
            df = pd.DataFrame(student['quiz_history'])
            df['submitted_at'] = pd.to_datetime(df['submitted_at'])
            df = df.sort_values('submitted_at')
            
            fig = px.line(
                df, 
                x='submitted_at', 
                y='score',
                title=f"{student['name']}'s Score Progression",
                markers=True
            )
            fig.update_traces(line_color='#11998e', line_width=3, marker_size=8)
            st.plotly_chart(fig, use_container_width=True)
            
            # Topic performance
            st.markdown("### 📚 Performance by Topic")
            topic_scores = {}
            for quiz in student['quiz_history']:
                topic = quiz['topic']
                if topic not in topic_scores:
                    topic_scores[topic] = []
                topic_scores[topic].append(quiz['score'])
            
            topic_avg = {topic: sum(scores)/len(scores) for topic, scores in topic_scores.items()}
            
            fig = px.bar(
                x=list(topic_avg.keys()),
                y=list(topic_avg.values()),
                title=f"{student['name']}'s Average Score by Topic",
                color=list(topic_avg.values()),
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed quiz history
            st.markdown("### 📝 Detailed Quiz History")
            history_df = pd.DataFrame(student['quiz_history'])
            history_df['submitted_at'] = pd.to_datetime(history_df['submitted_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(
                history_df[['topic', 'difficulty', 'score', 'correct_answers', 'total_questions', 'submitted_at']],
                use_container_width=True
            )

def render_quiz_management():
    """Render quiz management interface"""
    st.markdown("## 📝 Quiz Management")
    
    quiz_gen = QuizGenerator("http://localhost:8000/api")
    
    tab1, tab2, tab3 = st.tabs(["🎯 Generate Quiz", "📚 Quiz Templates", "📊 Quiz Analytics"])
    
    with tab1:
        st.markdown("### 🎯 Create New Quiz")
        
        # Quiz generation form
        quiz_params = quiz_gen.render_quiz_form()
        
        if quiz_params:
            with st.spinner("🤖 Generating quiz..."):
                quiz = quiz_gen.generate_quiz(
                    quiz_params['topic'],
                    quiz_params['difficulty'],
                    quiz_params['num_questions']
                )
                
                if quiz:
                    st.success("✅ Quiz generated successfully!")
                    
                    # Preview quiz
                    st.markdown("### 👀 Quiz Preview")
                    st.markdown(f"**Title:** {quiz['title']}")
                    st.markdown(f"**Topic:** {quiz['topic']}")
                    st.markdown(f"**Difficulty:** {quiz['difficulty']}/5")
                    st.markdown(f"**Questions:** {len(quiz['questions'])}")
                    
                    with st.expander("📋 View Questions"):
                        for i, question in enumerate(quiz['questions']):
                            st.markdown(f"**Q{i+1}:** {question['question']}")
                            for j, option in enumerate(question['options']):
                                st.markdown(f"   {chr(65+j)}) {option}")
                            st.markdown("---")
    
    with tab2:
        st.markdown("### 📚 Quiz Templates")
        
        # Predefined quiz templates
        templates = [
            {"name": "Python Basics", "topic": "Python Programming", "difficulty": 2, "questions": 10},
            {"name": "Data Structures", "topic": "Computer Science", "difficulty": 3, "questions": 8},
            {"name": "World History", "topic": "History", "difficulty": 3, "questions": 12},
            {"name": "Basic Mathematics", "topic": "Mathematics", "difficulty": 2, "questions": 15},
            {"name": "English Grammar", "topic": "English", "difficulty": 2, "questions": 10},
        ]
        
        for template in templates:
            with st.expander(f"📋 {template['name']}"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**Topic:** {template['topic']}")
                with col2:
                    st.write(f"**Difficulty:** {template['difficulty']}/5")
                with col3:
                    st.write(f"**Questions:** {template['questions']}")
                with col4:
                    if st.button(f"Generate", key=f"template_{template['name']}"):
                        with st.spinner("Generating from template..."):
                            quiz = quiz_gen.generate_quiz(
                                template['topic'],
                                template['difficulty'],
                                template['questions']
                            )
                            if quiz:
                                st.success(f"✅ {template['name']} quiz generated!")
    
    with tab3:
        st.markdown("### 📊 Quiz Analytics")
        
        # Mock quiz analytics data
        st.info("📊 Quiz analytics will show usage statistics, popular topics, and performance metrics.")
        
        # Sample analytics
        col1, col2 = st.columns(2)
        
        with col1:
            # Most popular topics
            topics = ["Python Programming", "Mathematics", "History", "Science", "English"]
            usage = [45, 38, 32, 28, 25]
            
            fig = px.bar(
                x=topics,
                y=usage,
                title="Most Popular Quiz Topics",
                labels={'x': 'Topic', 'y': 'Number of Quizzes Taken'},
                color=usage,
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Difficulty distribution
            difficulties = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]
            counts = [20, 35, 40, 25, 15]
            
            fig = px.pie(
                values=counts,
                names=difficulties,
                title="Quiz Difficulty Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

def render_content_library():
    """Render content library management"""
    st.markdown("## 📚 Content Library")
    
    tab1, tab2 = st.tabs(["📖 Browse Content", "➕ Add Content"])
    
    with tab1:
        st.markdown("### 📖 Available Content")
        
        # Mock content library
        content_items = [
            {"title": "Introduction to Python", "type": "Course", "topics": ["Programming", "Python"], "difficulty": 2},
            {"title": "World War II Overview", "type": "Lesson", "topics": ["History", "War"], "difficulty": 3},
            {"title": "Basic Algebra", "type": "Course", "topics": ["Mathematics", "Algebra"], "difficulty": 2},
            {"title": "Cell Biology", "type": "Lesson", "topics": ["Science", "Biology"], "difficulty": 3},
        ]
        
        for item in content_items:
            with st.expander(f"📋 {item['title']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Type:** {item['type']}")
                with col2:
                    st.write(f"**Topics:** {', '.join(item['topics'])}")
                with col3:
                    st.write(f"**Difficulty:** {item['difficulty']}/5")
                
                if st.button(f"Generate Quiz from {item['title']}", key=f"content_{item['title']}"):
                    st.info(f"Quiz generation from {item['title']} would be implemented here.")
    
    with tab2:
        st.markdown("### ➕ Add New Content")
        
        with st.form("add_content_form"):
            title = st.text_input("Content Title")
            content_type = st.selectbox("Content Type", ["Course", "Lesson", "Article", "Video"])
            topics = st.multiselect("Topics", ["Programming", "Mathematics", "Science", "History", "English", "Art"])
            difficulty = st.slider("Difficulty Level", 1, 5, 3)
            description = st.text_area("Description")
            
            if st.form_submit_button("📚 Add Content"):
                st.success(f"✅ Content '{title}' added successfully!")

def render_educator_settings():
    """Render educator settings"""
    st.markdown("## ⚙️ Educator Settings")
    
    user = st.session_state.user
    
    tab1, tab2, tab3 = st.tabs(["👤 Profile", "🎯 Preferences", "📊 Reports"])
    
    with tab1:
        st.markdown("### 👤 Profile Settings")
        
        with st.form("educator_profile_form"):
            name = st.text_input("Name", value=user.get('name', ''))
            email = st.text_input("Email", value=user.get('email', ''), disabled=True)
            institution = st.text_input("Institution", value="Demo University")
            department = st.text_input("Department", value="Computer Science")
            
            if st.form_submit_button("💾 Save Profile"):
                st.session_state.user['name'] = name
                st.success("✅ Profile updated successfully!")
    
    with tab2:
        st.markdown("### 🎯 Teaching Preferences")
        
        with st.form("teaching_preferences_form"):
            default_difficulty = st.slider("Default Quiz Difficulty", 1, 5, 3)
            default_questions = st.slider("Default Number of Questions", 5, 20, 10)
            auto_feedback = st.checkbox("Enable Automatic Feedback", value=True)
            email_notifications = st.checkbox("Email Notifications for Student Activity", value=True)
            
            if st.form_submit_button("💾 Save Preferences"):
                st.success("✅ Preferences saved successfully!")
    
    with tab3:
        st.markdown("### 📊 Generate Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📈 Class Performance Report", use_container_width=True):
                st.info("📊 Generating class performance report...")
                # Mock report generation
                st.success("✅ Report generated successfully!")
        
        with col2:
            if st.button("📅 Activity Summary Report", use_container_width=True):
                st.info("📊 Generating activity summary...")
                st.success("✅ Report generated successfully!")

def get_score_color(score):
    """Get color based on score"""
    if score >= 90:
        return "#28a745"
    elif score >= 70:
        return "#ffc107"
    elif score >= 50:
        return "#fd7e14"
    else:
        return "#dc3545"

def logout_user():
    """Logout user and clear session"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

if __name__ == "__main__":
    render_educator_dashboard()

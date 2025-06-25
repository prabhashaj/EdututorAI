# frontend/pages/educator_dashboard.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
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
    
    # Set default page to "Quiz Assignment" if not already set
    if 'educator_page' not in st.session_state:
        st.session_state.educator_page = "📝 Quiz Assignment"
    
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
        .big-button {
            background-color: #1E88E5;
            color: white;
            padding: 15px 20px;
            font-size: 18px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
            cursor: pointer;
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
        current_page = st.radio(
            "Go to:",
            ["📝 Quiz Assignment", "📊 Student Progress & Analysis", "📚 Quiz History"],
            key="educator_nav_radio",
            index=0 if st.session_state.educator_page == "📝 Quiz Assignment" else 
                  1 if st.session_state.educator_page == "📊 Student Progress & Analysis" else 2
        )
        
        # Update the current page after the widget is rendered
        st.session_state.educator_page = current_page
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
    
    # Route to different pages
    if st.session_state.educator_page == "📝 Quiz Assignment":
        render_quiz_assignment()
    elif st.session_state.educator_page == "📊 Student Progress & Analysis":
        render_student_progress_analysis()
    elif st.session_state.educator_page == "📚 Quiz History":
        render_quiz_history()

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
                    
                    # Store quiz in session
                    st.session_state.current_quiz = quiz
                    
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
                    
                    # Assign to students section
                    st.markdown("### 🎯 Assign Quiz to Students")
                    
                    # Hardcoded student list for demo
                    students = [
                        {"id": "student_id", "name": "Student User", "email": "student@edututor.ai"}
                    ]
                    
                    selected_students = []
                    for student in students:
                        if st.checkbox(f"{student['name']} ({student['email']})", value=True):
                            selected_students.append(student['id'])
                    
                    notification = st.text_area("Notification Message (Optional)", 
                                              value=f"New quiz on {quiz['topic']} has been assigned to you.")
                    
                    if st.button("📤 Assign Quiz to Selected Students", use_container_width=True):
                        if selected_students:
                            success = quiz_gen.assign_quiz(
                                quiz['id'],
                                selected_students,
                                notification
                            )
                            
                            if success:
                                st.success(f"✅ Quiz assigned to {len(selected_students)} student(s)!")
                            else:
                                st.error("❌ Failed to assign quiz")
                        else:
                            st.warning("⚠️ Please select at least one student")
    
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

def render_quiz_assignment():
    """Render quiz assignment interface"""
    st.markdown("## 📝 Quiz Assignment")
    
    # Create a simple, clear UI for creating and assigning quizzes
    quiz_gen = QuizGenerator("http://localhost:8000/api")
    
    # Main quiz creation form
    st.markdown("### 🎯 Create a New Quiz")
    st.markdown("Enter the details below to generate a new quiz for your students.")
    
    with st.form("quiz_generation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                topic = st.text_input(
                    "Topic",
                    placeholder="e.g., Python Programming, Mathematics, History",
                    help="Enter the subject or topic for your quiz"
                )
                
                difficulty = st.select_slider(
                    "Difficulty Level",
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    format_func=lambda x: {
                        1: "⭐ Very Easy",
                        2: "⭐⭐ Easy", 
                        3: "⭐⭐⭐ Medium",
                        4: "⭐⭐⭐⭐ Hard",
                        5: "⭐⭐⭐⭐⭐ Very Hard"
                    }[x]
                )
            
            with col2:
                num_questions = st.slider(
                    "Number of Questions",
                    min_value=3,
                    max_value=15,
                    value=5,
                    help="Choose how many questions you want in your quiz"
                )
                
                quiz_type = st.selectbox(
                    "Quiz Type",
                    ["Multiple Choice", "True/False", "Mixed"],
                    help="Select the type of questions"
                )
            
            generate_btn = st.form_submit_button(
                "🚀 Generate Quiz",
                use_container_width=True,
                type="primary"
            )
    
    # Quiz generation and preview
    if generate_btn and topic:
        with st.spinner("🤖 Generating quiz..."):
            quiz = quiz_gen.generate_quiz(
                topic,
                difficulty,
                num_questions
            )
            
            if quiz and isinstance(quiz, dict) and 'id' in quiz and 'questions' in quiz:
                # Store quiz in session for preview
                st.session_state.current_quiz = quiz
                # Show success message
                st.success("✅ Quiz generated successfully! Please review the questions below.")
            else:
                st.error("❌ Failed to generate quiz. Please try again with a different topic or settings.")
                # Clear any partial quiz data
                if 'current_quiz' in st.session_state:
                    del st.session_state.current_quiz
    else:
        if generate_btn:
            st.error("⚠️ Please enter a topic for your quiz!")
    
    # Display quiz preview if a quiz has been properly generated
    if ('current_quiz' in st.session_state and 
        st.session_state.current_quiz and 
        isinstance(st.session_state.current_quiz, dict) and
        'id' in st.session_state.current_quiz and
        'questions' in st.session_state.current_quiz):
        
        quiz = st.session_state.current_quiz
        
        st.markdown("---")
        st.markdown("### 👀 Quiz Preview")
        
        # Quiz details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Topic:** {quiz.get('topic', 'Unknown')}")
        with col2:
            st.info(f"**Difficulty:** {quiz.get('difficulty', 'Unknown')}/5")
        with col3:
            st.info(f"**Questions:** {len(quiz.get('questions', []))}")
        
        # Show questions for review
        st.markdown("#### 📋 Questions to Review:")
        questions = quiz.get('questions', [])
        for i, question in enumerate(questions):
            with st.expander(f"Question {i+1}: {question['question'][:60]}..."):
                st.markdown(f"**Q{i+1}:** {question['question']}")
                st.markdown("**Options:**")
                for j, option in enumerate(question.get('options', [])):
                    st.markdown(f"   {chr(65+j)}) {option}")
        
        st.markdown("---")
        
        # Assignment section
        st.markdown("### 👥 Assign Quiz to Students")
        st.markdown("Review the quiz above and assign it to your students when you're satisfied with the questions.")
        
        # Notification message for students
        notification_message = st.text_area(
            "Message to Students",
            value=f"A new quiz on {quiz.get('topic', 'this topic')} has been assigned to you. Please complete it at your earliest convenience.",
            help="This message will be shown to students when they see the assigned quiz"
        )
        
        # Student selection (hardcoded for demo)
        st.markdown("**Select Students:**")
        students = [
            {"id": "student_id", "name": "Student User", "email": "student@edututor.ai"}
        ]
        
        selected_students = []
        for student in students:
            if st.checkbox(f"✅ {student['name']} ({student['email']})", value=True, key=f"student_{student['id']}"):
                selected_students.append(student['id'])
        
        # Assignment button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📤 Assign Quiz to Selected Students", use_container_width=True, type="primary"):
                if selected_students and 'id' in quiz:
                    success = quiz_gen.assign_quiz(
                        quiz['id'],
                        selected_students,
                        notification_message
                    )
                    
                    if success:
                        st.success(f"✅ Quiz '{quiz.get('topic', 'Unknown')}' has been assigned to {len(selected_students)} student(s)!")
                        st.info("Students will see this quiz in their dashboard when they log in.")
                        # Clear the current quiz from session after successful assignment
                        del st.session_state.current_quiz
                        st.rerun()
                    else:
                        st.error("❌ Failed to assign quiz. Please try again.")
                elif not selected_students:
                    st.warning("⚠️ Please select at least one student to assign the quiz.")
                else:
                    st.error("❌ Quiz ID not found. Please generate a new quiz.")
        
        # Option to generate a new quiz
        st.markdown("---")
        if st.button("🔄 Generate a Different Quiz", use_container_width=True):
            # Clear quiz data
            if 'current_quiz' in st.session_state:
                del st.session_state.current_quiz
            st.rerun()

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

def render_student_progress_analysis():
    """Render student progress and analysis dashboard"""
    st.markdown("## 📊 Student Progress & Analysis")
    
    analytics = AnalyticsComponent("http://localhost:8000/api")
    students_data = analytics.get_students_analytics()
    
    if not students_data:
        st.info("👥 No student data available yet. Students need to take quizzes to generate analytics.")
        st.markdown("""
        ### Getting Started
        1. Go to the **Quiz Assignment** page
        2. Create and assign quizzes to students
        3. Once students complete quizzes, their progress will appear here
        """)
        return
    
    # Overall class metrics
    col1, col2, col3 = st.columns(3)
    
    total_students = len(students_data)
    active_students = len([s for s in students_data if s['total_quizzes'] > 0])
    total_quizzes = sum([s['total_quizzes'] for s in students_data])
    class_avg = sum([s['average_score'] for s in students_data if s['total_quizzes'] > 0]) / active_students if active_students > 0 else 0
    
    with col1:
        st.metric("👥 Total Students", total_students)
    
    with col2:
        st.metric("📝 Total Quizzes Taken", total_quizzes)
    
    with col3:
        st.metric("📊 Class Average Score", f"{class_avg:.1f}%")
    
    # Student list
    st.markdown("### 👥 Student Progress")
    
    # Add a search box for filtering students
    search = st.text_input("🔍 Search Students", placeholder="Filter by name or email...")
    
    # Filter and display students
    filtered_students = students_data
    if search:
        filtered_students = [s for s in students_data if search.lower() in s['name'].lower() or search.lower() in s['email'].lower()]
    
    if not filtered_students:
        st.warning("No students match your search criteria.")
    
    for student in filtered_students:
        with st.expander(f"👤 {student['name']} ({student['email']})"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📚 Quizzes Taken", student['total_quizzes'])
            with col2:
                st.metric("📊 Average Score", f"{student['average_score']:.1f}%")
            with col3:
                st.metric("⬆️ Highest Score", f"{student['highest_score']:.1f}%")
            with col4:
                st.metric("⬇️ Lowest Score", f"{student['lowest_score']:.1f}%")
            
            # Score progression chart
            if student['quiz_history']:
                st.markdown("#### 📈 Score Progression")
                scores = [q['score'] for q in student['quiz_history']]
                dates = [q['submitted_at'][:10] for q in student['quiz_history']]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates, 
                    y=scores,
                    mode='lines+markers',
                    name='Score'
                ))
                fig.update_layout(
                    title=f"{student['name']}'s Score Progression",
                    xaxis_title="Date",
                    yaxis_title="Score (%)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Topic performance
                st.markdown("#### 📚 Performance by Topic")
                topic_scores = {}
                for quiz in student['quiz_history']:
                    topic = quiz['topic']
                    if topic not in topic_scores:
                        topic_scores[topic] = []
                    topic_scores[topic].append(quiz['score'])
                
                if topic_scores:
                    topic_avg = {topic: sum(scores)/len(scores) for topic, scores in topic_scores.items()}
                    
                    fig = px.bar(
                        x=list(topic_avg.keys()),
                        y=list(topic_avg.values()),
                        title=f"{student['name']}'s Average Score by Topic",
                        labels={'x': 'Topic', 'y': 'Average Score (%)'},
                        color=list(topic_avg.values()),
                        color_continuous_scale='RdYlGn'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Detailed quiz history
                st.markdown("#### 📝 Detailed Quiz History")
                history_df = pd.DataFrame(student['quiz_history'])
                history_df['submitted_at'] = pd.to_datetime(history_df['submitted_at']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(
                    history_df[['topic', 'difficulty', 'score', 'correct_answers', 'total_questions', 'submitted_at']],
                    use_container_width=True
                )

def render_quiz_history():
    """Render quiz history for educator"""
    st.markdown("## 📚 Quiz History")
    st.markdown("View all quizzes created and assigned to students")
    
    analytics = AnalyticsComponent("http://localhost:8000/api")
    students_data = analytics.get_students_analytics()
    
    if not students_data:
        st.info("No quiz history available yet. Quizzes will appear here after they are created and assigned.")
        return
    
    # Get all unique quizzes from student histories
    all_quizzes = {}
    quiz_completion_data = {}
    
    for student in students_data:
        if student['quiz_history']:
            for quiz in student['quiz_history']:
                quiz_id = quiz.get('quiz_id')
                if quiz_id not in all_quizzes:
                    all_quizzes[quiz_id] = {
                        'quiz_id': quiz_id,
                        'topic': quiz.get('topic', 'Unknown'),
                        'difficulty': quiz.get('difficulty', 'Unknown'),
                        'created_at': quiz.get('created_at', 'Unknown'),
                        'total_submissions': 0,
                        'avg_score': 0,
                        'completion_rate': 0
                    }
                    quiz_completion_data[quiz_id] = {
                        'submissions': 0,
                        'total_score': 0,
                        'students': set()
                    }
                
                # Update quiz stats
                quiz_completion_data[quiz_id]['submissions'] += 1
                quiz_completion_data[quiz_id]['total_score'] += quiz.get('score', 0)
                quiz_completion_data[quiz_id]['students'].add(student['id'])
    
    # Calculate averages and format the data
    for quiz_id, data in quiz_completion_data.items():
        if data['submissions'] > 0:
            all_quizzes[quiz_id]['total_submissions'] = data['submissions']
            all_quizzes[quiz_id]['avg_score'] = data['total_score'] / data['submissions']
            all_quizzes[quiz_id]['completion_rate'] = len(data['students'])
    
    # Convert to list and sort by date (newest first)
    quiz_list = list(all_quizzes.values())
    quiz_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Display quiz history
    if not quiz_list:
        st.info("No completed quizzes found. Quizzes will appear here after students complete them.")
        return
    
    # Show filters
    col1, col2 = st.columns(2)
    with col1:
        topic_filter = st.multiselect(
            "Filter by Topic",
            options=sorted(set(q['topic'] for q in quiz_list)),
            default=[]
        )
    
    with col2:
        difficulty_filter = st.multiselect(
            "Filter by Difficulty",
            options=sorted(set(q['difficulty'] for q in quiz_list)),
            default=[]
        )
    
    # Apply filters
    filtered_quizzes = quiz_list
    if topic_filter:
        filtered_quizzes = [q for q in filtered_quizzes if q['topic'] in topic_filter]
    if difficulty_filter:
        filtered_quizzes = [q for q in filtered_quizzes if q['difficulty'] in difficulty_filter]
    
    # Display quiz cards
    st.markdown("### 📝 Quiz List")
    
    if not filtered_quizzes:
        st.warning("No quizzes match the selected filters.")
    else:
        # Convert to DataFrame for easier display
        df = pd.DataFrame(filtered_quizzes)
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Format columns
        if 'avg_score' in df.columns:
            df['avg_score'] = df['avg_score'].apply(lambda x: f"{x:.1f}%")
        
        # Rename columns for better display
        columns_to_display = {
            'topic': 'Topic',
            'difficulty': 'Difficulty',
            'created_at': 'Created At',
            'total_submissions': 'Submissions',
            'avg_score': 'Avg. Score',
            'completion_rate': 'Students Completed'
        }
        
        df_display = df.rename(columns=columns_to_display)
        column_order = [col for col in columns_to_display.values() if col in df_display.columns]
        
        st.dataframe(
            df_display[column_order],
            use_container_width=True,
            hide_index=True
        )
        
        # Add detail view for selected quiz
        if 'quiz_id' in df.columns:
            selected_quiz_id = st.selectbox(
                "Select a quiz to view details",
                options=df['quiz_id'].tolist(),
                format_func=lambda x: f"{df[df['quiz_id'] == x]['topic'].iloc[0]} - {df[df['quiz_id'] == x]['difficulty'].iloc[0]}"
            )
            
            if selected_quiz_id:
                st.markdown("### 📊 Quiz Details")
                
                # Find all students who took this quiz
                students_who_completed = []
                for student in students_data:
                    for quiz in student.get('quiz_history', []):
                        if quiz.get('quiz_id') == selected_quiz_id:
                            students_who_completed.append({
                                'student_name': student['name'],
                                'student_id': student['id'],
                                'score': quiz.get('score', 0),
                                'submitted_at': quiz.get('submitted_at', '')
                            })
                
                if students_who_completed:
                    # Show student performance for this quiz
                    student_df = pd.DataFrame(students_who_completed)
                    if 'submitted_at' in student_df.columns:
                        student_df['submitted_at'] = pd.to_datetime(student_df['submitted_at']).dt.strftime('%Y-%m-%d %H:%M')
                    
                    student_df = student_df.rename(columns={
                        'student_name': 'Student Name',
                        'score': 'Score (%)',
                        'submitted_at': 'Submitted At'
                    })
                    
                    st.dataframe(
                        student_df[['Student Name', 'Score (%)', 'Submitted At']],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Score distribution chart
                    scores = [s['score'] for s in students_who_completed]
                    
                    fig = px.histogram(
                        scores,
                        nbins=10,
                        title='Distribution of Scores for Selected Quiz',
                        labels={'value': 'Score (%)', 'count': 'Number of Students'},
                        color_discrete_sequence=['#11998e']
                    )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No students have completed this quiz yet.")

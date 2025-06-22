# frontend/components/analytics.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict
import requests

class AnalyticsComponent:
    """Handle analytics and data visualization"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
    
    def get_quiz_history(self, user_id: str) -> List[Dict]:
        """Get user's quiz history"""
        try:
            response = requests.get(f"{self.api_base_url}/quiz/history/{user_id}")
            if response.status_code == 200:
                return response.json().get("history", [])
            return []
        except:
            return []
    
    def get_students_analytics(self) -> List[Dict]:
        """Get all students analytics"""
        try:
            response = requests.get(f"{self.api_base_url}/quiz/analytics/students")
            if response.status_code == 200:
                return response.json().get("students", [])
            return []
        except:
            return []
    
    def render_student_analytics(self, user_id: str):
        """Render student analytics dashboard"""
        history = self.get_quiz_history(user_id)
        
        if not history:
            st.info("📊 No quiz data available yet. Take some quizzes to see your analytics!")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_quizzes = len(history)
        avg_score = sum([q['score'] for q in history]) / total_quizzes
        best_score = max([q['score'] for q in history])
        topics_covered = len(set([q['topic'] for q in history]))
        
        with col1:
            st.metric("📚 Total Quizzes", total_quizzes)
        with col2:
            st.metric("📊 Average Score", f"{avg_score:.1f}%")
        with col3:
            st.metric("🏆 Best Score", f"{best_score:.1f}%")
        with col4:
            st.metric("🎯 Topics Covered", topics_covered)
        
        # Performance over time
        if len(history) > 1:
            st.subheader("📈 Performance Trend")
            df = pd.DataFrame(history)
            df['submitted_at'] = pd.to_datetime(df['submitted_at'])
            df = df.sort_values('submitted_at')
            
            fig = px.line(
                df, 
                x='submitted_at', 
                y='score',
                title='Quiz Scores Over Time',
                labels={'submitted_at': 'Date', 'score': 'Score (%)'},
                line_shape='spline'
            )
            fig.update_traces(line_color='#667eea', line_width=3)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Topic performance
        st.subheader("📚 Performance by Topic")
        topic_scores = {}
        for quiz in history:
            topic = quiz['topic']
            if topic not in topic_scores:
                topic_scores[topic] = []
            topic_scores[topic].append(quiz['score'])
        
        topic_avg = {topic: sum(scores)/len(scores) for topic, scores in topic_scores.items()}
        
        fig = px.bar(
            x=list(topic_avg.keys()),
            y=list(topic_avg.values()),
            title='Average Score by Topic',
            labels={'x': 'Topic', 'y': 'Average Score (%)'},
            color=list(topic_avg.values()),
            color_continuous_scale='Viridis'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Difficulty analysis
        st.subheader("⭐ Performance by Difficulty")
        difficulty_scores = {}
        for quiz in history:
            diff = quiz['difficulty']
            if diff not in difficulty_scores:
                difficulty_scores[diff] = []
            difficulty_scores[diff].append(quiz['score'])
        
        difficulty_avg = {f"Level {diff}": sum(scores)/len(scores) for diff, scores in difficulty_scores.items()}
        
        fig = px.scatter(
            x=list(difficulty_scores.keys()),
            y=[sum(scores)/len(scores) for scores in difficulty_scores.values()],
            size=[len(scores) for scores in difficulty_scores.values()],
            title='Performance vs Difficulty Level',
            labels={'x': 'Difficulty Level', 'y': 'Average Score (%)'},
            color=[sum(scores)/len(scores) for scores in difficulty_scores.values()],
            color_continuous_scale='RdYlBu_r'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def render_educator_analytics(self):
        """Render educator analytics dashboard"""
        students_data = self.get_students_analytics()
        
        if not students_data:
            st.info("👥 No student data available yet.")
            return
        
        # Class overview
        col1, col2, col3, col4 = st.columns(4)
        
        total_students = len(students_data)
        active_students = len([s for s in students_data if s['total_quizzes'] > 0])
        total_quizzes = sum([s['total_quizzes'] for s in students_data])
        class_avg = sum([s['average_score'] for s in students_data if s['total_quizzes'] > 0]) / active_students if active_students > 0 else 0
        
        with col1:
            st.metric("👥 Total Students", total_students)
        with col2:
            st.metric("🎯 Active Students", active_students)
        with col3:
            st.metric("📝 Total Quizzes", total_quizzes)
        with col4:
            st.metric("📊 Class Average", f"{class_avg:.1f}%")
        
        # Student performance distribution
        if active_students > 0:
            st.subheader("📊 Class Performance Distribution")
            scores = [s['average_score'] for s in students_data if s['total_quizzes'] > 0]
            
            fig = px.histogram(
                scores,
                nbins=10,
                title='Distribution of Student Average Scores',
                labels={'value': 'Average Score (%)', 'count': 'Number of Students'},
                color_discrete_sequence=['#667eea']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Top performers
        st.subheader("🏆 Top Performers")
        top_students = sorted(
            [s for s in students_data if s['total_quizzes'] > 0],
            key=lambda x: x['average_score'],
            reverse=True
        )[:10]
        
        if top_students:
            for i, student in enumerate(top_students):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                with col1:
                    st.write(f"**{i+1}. {student['name']}**")
                with col2:
                    st.write(f"{student['average_score']:.1f}%")
                with col3:
                    st.write(f"{student['total_quizzes']} quizzes")
                with col4:
                    if student['quiz_history']:
                        latest = student['quiz_history'][0]['submitted_at'][:10]
                        st.write(f"Last: {latest}")
        
        # Activity heatmap
        st.subheader("📅 Quiz Activity Heatmap")
        if students_data:
            all_quizzes = []
            for student in students_data:
                for quiz in student['quiz_history']:
                    quiz['student_name'] = student['name']
                    all_quizzes.append(quiz)
            
            if all_quizzes:
                df = pd.DataFrame(all_quizzes)
                df['submitted_at'] = pd.to_datetime(df['submitted_at'])
                df['date'] = df['submitted_at'].dt.date
                df['hour'] = df['submitted_at'].dt.hour
                
                activity = df.groupby(['date', 'hour']).size().reset_index(name='count')
                
                if not activity.empty:
                    fig = px.density_heatmap(
                        activity,
                        x='hour',
                        y='date',
                        z='count',
                        title='Quiz Activity by Time',
                        labels={'hour': 'Hour of Day', 'date': 'Date', 'count': 'Quiz Count'}
                    )
                    st.plotly_chart(fig, use_container_width=True)

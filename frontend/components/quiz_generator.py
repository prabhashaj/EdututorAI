# frontend/components/quiz_generator.py
import streamlit as st
import requests
from typing import Dict, List, Optional

class QuizGenerator:
    """Handle quiz generation and management"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
    
    def generate_quiz(self, topic: str, difficulty: int, num_questions: int) -> Optional[Dict]:
        """Generate a new quiz"""
        try:
            response = requests.post(
                f"{self.api_base_url}/quiz/generate",
                json={
                    "topic": topic,
                    "difficulty": difficulty,
                    "num_questions": num_questions
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to generate quiz: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Quiz generation error: {str(e)}")
            return None
    
    def submit_quiz(self, quiz_id: str, user_id: str, answers: Dict) -> Optional[Dict]:
        """Submit quiz answers"""
        try:
            response = requests.post(
                f"{self.api_base_url}/quiz/submit",
                json={
                    "quiz_id": quiz_id,
                    "user_id": user_id,
                    "answers": answers
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to submit quiz: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Quiz submission error: {str(e)}")
            return None
    
    def render_quiz_form(self) -> Optional[Dict]:
        """Render quiz generation form"""
        with st.form("quiz_generation_form"):
            st.subheader("🎯 Generate New Quiz")
            
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
            
            submitted = st.form_submit_button(
                "🚀 Generate Quiz",
                use_container_width=True,
                type="primary"
            )
            
            if submitted and topic:
                return {
                    "topic": topic,
                    "difficulty": difficulty,
                    "num_questions": num_questions,
                    "quiz_type": quiz_type
                }
            elif submitted:
                st.error("Please enter a topic for your quiz!")
                
        return None
    
    def render_quiz_interface(self, quiz: Dict) -> Optional[Dict]:
        """Render quiz taking interface"""
        st.subheader(f"📝 {quiz['title']}")
        
        # Quiz info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Topic:** {quiz['topic']}")
        with col2:
            st.info(f"**Difficulty:** {quiz['difficulty']}/5")
        with col3:
            st.info(f"**Questions:** {len(quiz['questions'])}")
        
        st.markdown("---")
        
        # Quiz questions
        answers = {}
        
        with st.form("quiz_submission_form"):
            for i, question in enumerate(quiz['questions']):
                st.markdown(f"### Question {i+1}")
                st.markdown(f"**{question['question']}**")
                
                # Radio buttons for options
                selected_answer = st.radio(
                    f"Choose your answer:",
                    question['options'],
                    key=f"question_{i}",
                    index=None
                )
                
                if selected_answer:
                    answers[i] = selected_answer
                
                st.markdown("---")
            
            # Progress indicator
            progress = len(answers) / len(quiz['questions'])
            st.progress(progress)
            st.caption(f"Answered: {len(answers)}/{len(quiz['questions'])} questions")
            
            # Submit buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                submitted = st.form_submit_button(
                    "✅ Submit Quiz",
                    use_container_width=True,
                    type="primary",
                    disabled=len(answers) != len(quiz['questions'])
                )
            
            if submitted:
                return answers
                
        return None
    
    def render_quiz_result(self, result: Dict):
        """Render quiz results"""
        st.balloons()
        
        # Score display
        score = result['score']
        if score >= 90:
            score_color = "🟢"
            message = "Excellent work! 🎉"
        elif score >= 70:
            score_color = "🟡"
            message = "Good job! 👍"
        elif score >= 50:
            score_color = "🟠"
            message = "Not bad, keep practicing! 💪"
        else:
            score_color = "🔴"
            message = "Keep studying, you'll improve! 📚"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 1rem;
            text-align: center;
            color: white;
            margin: 1rem 0;
        ">
            <h1>{score_color} {score:.1f}%</h1>
            <h3>{message}</h3>
            <p>You got {result['correct_answers']} out of {result['total_questions']} questions correct!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Detailed feedback
        with st.expander("📋 Detailed Feedback", expanded=True):
            for i, feedback in enumerate(result['feedback']):
                if "Correct" in feedback:
                    st.success(f"✅ {feedback}")
                else:
                    st.error(f"❌ {feedback}")

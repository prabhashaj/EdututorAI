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
            payload = {
                "quiz_id": quiz_id,
                "user_id": user_id,
                "answers": answers
            }
            
            response = requests.post(
                f"{self.api_base_url}/quiz/submit",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                st.success("✅ Quiz submitted successfully!")
                return result
            else:
                st.error(f"❌ Failed to submit quiz: Status {response.status_code}")
                st.error(f"Error details: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. Please try again.")
            return None
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to server. Please check if the backend is running.")
            return None
        except Exception as e:
            st.error(f"❌ Error submitting quiz: {str(e)}")
            return None
    
    def assign_quiz(self, quiz_id: str, student_ids: list, notification_message: str = "") -> bool:
        """Assign a quiz to students"""
        try:
            response = requests.post(
                f"{self.api_base_url}/quiz/assign",
                json={
                    "quiz_id": quiz_id,
                    "student_ids": student_ids,
                    "notification_message": notification_message
                }
            )
            
            if response.status_code == 200:
                return True
            else:
                st.error(f"Failed to assign quiz: {response.text}")
                return False
                
        except Exception as e:
            st.error(f"Quiz assignment error: {str(e)}")
            return False
    
    def get_students(self, access_token: str) -> Optional[List[Dict]]:
        """Get list of all students for assignment"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            response = requests.get(
                f"{self.api_base_url}/classroom/students",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("students", [])
            else:
                st.error(f"Failed to get students: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Error getting students: {str(e)}")
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
    
    def render_quiz_interface(self, quiz: Optional[Dict]) -> Optional[Dict]:
        """Render quiz taking interface"""
        if not quiz:
            st.info("No quiz is currently selected. Please select a quiz to begin.")
            return None
            
        st.subheader(f"📝 {quiz.get('title', quiz.get('topic', 'Quiz'))}")
        
        # Quiz info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Topic:** {quiz.get('topic', 'Unknown')}")
        with col2:
            st.info(f"**Difficulty:** {quiz.get('difficulty', 'Unknown')}/5")
        with col3:
            st.info(f"**Questions:** {len(quiz.get('questions', []))}")
        
        st.markdown("---")
        
        # Quiz questions with form
        questions = quiz.get('questions', [])
        if not questions:
            st.error("No questions found in this quiz.")
            return None
        
        answers = {}
        
        with st.form("quiz_submission_form"):
            for i, question in enumerate(questions):
                st.markdown(f"### Question {i+1}")
                st.markdown(f"**{question['question']}**")
                
                # Radio buttons for options
                options = question.get('options', [])
                if not options:
                    st.error(f"No options found for question {i+1}")
                    continue
                
                selected_answer = st.radio(
                    "Choose your answer:",
                    options,
                    key=f"question_{i}",
                    index=None
                )
                
                if selected_answer:
                    answers[str(i)] = selected_answer
                
                st.markdown("---")
            
            # Simple submit button - always enabled
            st.markdown("### Submit Your Quiz")
            st.info("Make sure you have answered all questions before submitting.")
            
            submitted = st.form_submit_button(
                "✅ Submit Quiz",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                # Check if all questions are answered
                if len(answers) == len(questions):
                    return answers
                else:
                    st.error(f"⚠️ Please answer all {len(questions)} questions. You have answered {len(answers)} questions.")
                    return None
        
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

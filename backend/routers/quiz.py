# backend/routers/quiz.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid
from datetime import datetime

from models.quiz import QuizRequest, Quiz, QuizSubmission, QuizResult
from services.pinecone_service import PineconeService
from utils.config import settings
from services.gemini_service import GeminiService

router = APIRouter()
pinecone_service = PineconeService()
gemini_service = GeminiService(api_key=settings.gemini_api_key)

# In-memory storage for demo (use database in production)
quiz_storage = {}
quiz_results = {}

@router.post("/generate", response_model=Quiz)
async def generate_quiz(request: QuizRequest):
    """Generate a new quiz using Gemini 1.5 Flash model"""
    try:
        print(f"Generating quiz for topic: {request.topic}, difficulty: {request.difficulty}, questions: {request.num_questions}")
        
        # Generate quiz text using Gemini
        quiz_text = gemini_service.generate_quiz(request.topic, request.difficulty, request.num_questions)
        print("Raw model output:\n", quiz_text)
        
        # Parse questions from the generated text
        parsed_questions = GeminiService.parse_quiz_output(quiz_text)
        print(f"Parsed {len(parsed_questions)} questions")
        
        # Validate that we have questions
        if not parsed_questions:
            raise HTTPException(status_code=500, detail="Failed to generate valid questions")
        
        # Create quiz object
        quiz_id = str(uuid.uuid4())
        quiz = Quiz(
            id=quiz_id,
            title=f"Quiz on {request.topic}",
            topic=request.topic,
            difficulty=request.difficulty,
            questions=parsed_questions,
            created_at=datetime.now()
        )
        
        # Store quiz
        quiz_storage[quiz_id] = quiz
        
        # Return quiz without correct answers for frontend
        quiz_for_frontend = quiz.dict()
        for question in quiz_for_frontend["questions"]:
            question.pop("correct_answer", None)
            question.pop("explanation", None)
        
        print(f"Successfully created quiz with ID: {quiz_id}")
        return Quiz(**quiz_for_frontend)
        
    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

@router.post("/submit", response_model=QuizResult)
async def submit_quiz(submission: QuizSubmission):
    """Submit quiz answers and get results"""
    try:
        if submission.quiz_id not in quiz_storage:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        quiz = quiz_storage[submission.quiz_id]
        correct_answers = 0
        feedback = []
        
        print(f"Evaluating quiz submission for quiz_id: {submission.quiz_id}")
        print(f"User answers: {submission.answers}")
        
        for i, question in enumerate(quiz.questions):
            # Try both string and integer keys for answers
            user_answer = submission.answers.get(str(i)) or submission.answers.get(i, "")
            correct_answer_letter = question.correct_answer
            
            print(f"Question {i+1}: '{question.question}'")
            print(f"Options: {question.options}")
            print(f"Correct answer letter: {correct_answer_letter}")
            print(f"User answer: '{user_answer}'")
            
            # Convert letter to actual option text for comparison
            correct_answer_text = ""
            if correct_answer_letter in ['A', 'B', 'C', 'D']:
                option_index = ord(correct_answer_letter) - ord('A')  # A=0, B=1, C=2, D=3
                if 0 <= option_index < len(question.options):
                    correct_answer_text = question.options[option_index]
            
            print(f"Correct answer text: '{correct_answer_text}'")
            
            # Compare user answer with correct answer text
            is_correct = user_answer.strip() == correct_answer_text.strip()
            print(f"Is correct: {is_correct}")
            print("---")
            
            if is_correct:
                correct_answers += 1
                feedback.append(f"Question {i+1}: ✅ Correct! {question.explanation}")
            else:
                feedback.append(f"Question {i+1}: ❌ Incorrect. You answered: '{user_answer}'. Correct answer: {correct_answer_letter}) {correct_answer_text}. {question.explanation}")
        
        score = (correct_answers / len(quiz.questions)) * 100
        
        result = QuizResult(
            quiz_id=submission.quiz_id,
            user_id=submission.user_id,
            score=score,
            total_questions=len(quiz.questions),
            correct_answers=correct_answers,
            feedback=feedback,
            submitted_at=datetime.now()
        )
        
        # Store result
        result_id = f"{submission.user_id}_{submission.quiz_id}"
        quiz_results[result_id] = result
        
        # Mark assignment as completed
        if hasattr(assign_quiz, 'student_assignments') and submission.user_id in assign_quiz.student_assignments:
            for assignment in assign_quiz.student_assignments[submission.user_id]:
                if assignment['quiz_id'] == submission.quiz_id:
                    assignment['completed'] = True
                    assignment['completed_at'] = datetime.now().isoformat()
                    assignment['score'] = score
        
        # Store in Pinecone (skip if fails)
        try:
            await pinecone_service.store_quiz_result(
                user_id=submission.user_id,
                quiz_data=quiz.dict(),
                result_data=result.dict()
            )
        except Exception as pinecone_error:
            print(f"Warning: Failed to store in Pinecone: {pinecone_error}")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz: {str(e)}")

@router.post("/assign")
async def assign_quiz(assignment: dict):
    """Assign quiz to students"""
    try:
        quiz_id = assignment.get("quiz_id")
        student_ids = assignment.get("student_ids", [])
        notification_message = assignment.get("notification_message", "")
        
        if not quiz_id or quiz_id not in quiz_storage:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Store assignment records
        quiz = quiz_storage[quiz_id]
        assignment_id = str(uuid.uuid4())
        
        # In-memory storage for assignments
        if not hasattr(assign_quiz, 'assignments'):
            assign_quiz.assignments = {}
            
        if not hasattr(assign_quiz, 'student_assignments'):
            assign_quiz.student_assignments = {}
        
        # Store the assignment
        assign_quiz.assignments[assignment_id] = {
            "quiz_id": quiz_id,
            "student_ids": student_ids,
            "notification_message": notification_message,
            "assigned_at": datetime.now().isoformat()
        }
        
        # Store for each student
        for student_id in student_ids:
            if student_id not in assign_quiz.student_assignments:
                assign_quiz.student_assignments[student_id] = []
            
            assign_quiz.student_assignments[student_id].append({
                "assignment_id": assignment_id,
                "quiz_id": quiz_id,
                "quiz_title": quiz.title,
                "quiz_topic": quiz.topic,
                "notification_message": notification_message,
                "assigned_at": datetime.now().isoformat(),
                "completed": False
            })
        
        return {"message": f"Quiz assigned to {len(student_ids)} students", "assignment_id": assignment_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign quiz: {str(e)}")

@router.get("/history/{user_id}")
async def get_quiz_history(user_id: str):
    """Get quiz history for a user"""
    try:
        # Get quiz results from local storage first
        user_history = []
        for result_id, result in quiz_results.items():
            if result.user_id == user_id:
                # Get quiz details
                quiz = quiz_storage.get(result.quiz_id)
                if quiz:
                    history_item = {
                        "quiz_id": result.quiz_id,
                        "topic": quiz.topic,
                        "difficulty": quiz.difficulty,
                        "score": result.score,
                        "total_questions": result.total_questions,
                        "correct_answers": result.correct_answers,
                        "submitted_at": result.submitted_at.isoformat(),
                        "feedback": result.feedback
                    }
                    user_history.append(history_item)
        
        # Sort by submission date (newest first)
        user_history.sort(key=lambda x: x['submitted_at'], reverse=True)
        
        # If no local history, try Pinecone as fallback
        if not user_history:
            try:
                pinecone_history = await pinecone_service.get_user_quiz_history(user_id)
                user_history = pinecone_history
            except:
                pass  # Ignore Pinecone errors
        
        return {"history": user_history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quiz history: {str(e)}")

@router.get("/analytics/students")
async def get_students_analytics():
    """Get analytics for all students (educator view)"""
    try:
        students_data = await pinecone_service.get_all_students_data()
        return {"students": students_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/assignments/{student_id}")
async def get_student_assignments(student_id: str):
    """Get quizzes assigned to a student"""
    try:
        if not hasattr(assign_quiz, 'student_assignments'):
            assign_quiz.student_assignments = {}
            
        assignments = assign_quiz.student_assignments.get(student_id, [])
        return {"assignments": assignments}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assignments: {str(e)}")

@router.get("/{quiz_id}")
async def get_quiz_by_id(quiz_id: str):
    """Get quiz by ID"""
    try:
        if quiz_id not in quiz_storage:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        quiz = quiz_storage[quiz_id]
        
        # Create a copy of the quiz that doesn't include correct answers
        quiz_for_frontend = quiz.dict()
        for question in quiz_for_frontend["questions"]:
            question.pop("correct_answer", None)
            question.pop("explanation", None)
        
        return quiz_for_frontend
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve quiz: {str(e)}")

@router.get("/list")
async def list_quizzes():
    """Get a list of all available quizzes"""
    try:
        quizzes = []
        for quiz_id, quiz in quiz_storage.items():
            # Create a copy of the quiz that doesn't include correct answers
            quiz_copy = quiz.dict()
            for question in quiz_copy["questions"]:
                question.pop("correct_answer", None)
                question.pop("explanation", None)
            
            quizzes.append(quiz_copy)
        
        return {"quizzes": quizzes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list quizzes: {str(e)}")

@router.get("/assignments")
async def list_assignments():
    """Get a list of all quiz assignments"""
    try:
        if not hasattr(assign_quiz, 'assignments'):
            assign_quiz.assignments = {}
            
        assignments = []
        for assignment_id, assignment in assign_quiz.assignments.items():
            quiz_id = assignment.get('quiz_id')
            if quiz_id in quiz_storage:
                quiz = quiz_storage[quiz_id]
                
                assignments.append({
                    "id": assignment_id,
                    "quiz_id": quiz_id,
                    "title": quiz.title,
                    "topic": quiz.topic,
                    "assigned_date": assignment.get('assigned_at', "").split('T')[0],
                    "students": len(assignment.get('student_ids', [])),
                    "notification_message": assignment.get('notification_message', "")
                })
        
        return {"assignments": assignments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list assignments: {str(e)}")

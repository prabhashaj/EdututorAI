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
        prompt = GeminiService.build_prompt(request.topic, request.difficulty, request.num_questions)
        quiz_text = gemini_service.generate_quiz(request.topic, request.difficulty, request.num_questions)
        print("Raw model output:\n", quiz_text)
        parsed_questions = GeminiService.parse_quiz_output(quiz_text)

        quiz_id = str(uuid.uuid4())
        quiz = Quiz(
            id=quiz_id,
            title=f"Quiz on {request.topic}",
            topic=request.topic,
            difficulty=request.difficulty,
            questions=parsed_questions,
            created_at=datetime.now()
        )
        quiz_storage[quiz_id] = quiz
        quiz_for_frontend = quiz.dict()
        for question in quiz_for_frontend["questions"]:
            question.pop("correct_answer", None)
            question.pop("explanation", None)
        return Quiz(**quiz_for_frontend)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit", response_model=QuizResult)
async def submit_quiz(submission: QuizSubmission):
    """Submit quiz answers and get results"""
    try:
        if submission.quiz_id not in quiz_storage:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        quiz = quiz_storage[submission.quiz_id]
        correct_answers = 0
        feedback = []
        
        for i, question in enumerate(quiz.questions):
            user_answer = submission.answers.get(i, "")
            correct_answer = question.correct_answer
            
            if user_answer == correct_answer:
                correct_answers += 1
                feedback.append(f"Question {i+1}: Correct! {question.explanation}")
            else:
                feedback.append(f"Question {i+1}: Incorrect. Correct answer: {correct_answer}. {question.explanation}")
        
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
        
        # Store in Pinecone
        await pinecone_service.store_quiz_result(
            user_id=submission.user_id,
            quiz_data=quiz.dict(),
            result_data=result.dict()
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz: {str(e)}")

@router.get("/history/{user_id}")
async def get_quiz_history(user_id: str):
    """Get quiz history for a user"""
    try:
        history = await pinecone_service.get_user_quiz_history(user_id)
        return {"history": history}
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

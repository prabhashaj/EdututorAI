# backend/models/quiz.py
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None

class Quiz(BaseModel):
    id: Optional[str] = None
    title: str
    topic: str
    difficulty: int
    questions: List[QuizQuestion]
    created_at: Optional[datetime] = None

class QuizRequest(BaseModel):
    topic: str
    difficulty: int
    num_questions: int = 5

class QuizSubmission(BaseModel):
    quiz_id: str
    user_id: str
    answers: Dict[int, str]  # question_index: selected_answer
    submitted_at: Optional[datetime] = None

class QuizResult(BaseModel):
    quiz_id: str
    user_id: str
    score: float
    total_questions: int
    correct_answers: int
    feedback: List[str]
    submitted_at: datetime

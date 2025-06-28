# backend/routers/classroom.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
import json

from services.classroom_service import ClassroomService
from routers.auth import get_current_user, users_db
from models.user import User

router = APIRouter()

@router.post("/sync")
async def sync_classroom(
    access_token: str,
    current_user: User = Depends(get_current_user)
):
    """Sync courses from Google Classroom"""
    try:
        classroom_service = ClassroomService()
        courses = await classroom_service.sync_courses(access_token)
        
        return {
            "message": "Courses synced successfully",
            "courses": courses
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync classroom: {str(e)}")

@router.get("/courses")
async def get_courses(current_user: User = Depends(get_current_user)):
    """Get user's courses"""
    try:
        # For demo purposes, return mock courses
        mock_courses = [
            {
                "id": "course_1",
                "name": "Introduction to Python",
                "description": "Learn Python programming basics",
                "enrollmentCode": "ABC123"
            },
            {
                "id": "course_2", 
                "name": "Data Science Fundamentals",
                "description": "Introduction to data science concepts",
                "enrollmentCode": "DEF456"
            },
            {
                "id": "course_3",
                "name": "Web Development",
                "description": "Build modern web applications",
                "enrollmentCode": "GHI789"
            }
        ]
        
        return {"courses": mock_courses}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get courses: {str(e)}")

@router.get("/students")
async def get_all_students(current_user: User = Depends(get_current_user)):
    """Get all students in the system (for educators to assign quizzes)"""
    try:
        # Only allow educators to access this endpoint
        if current_user.get("role") != "educator":
            raise HTTPException(status_code=403, detail="Only educators can access student list")
        
        # Get all students from users_db
        students = []
        for user_id, user_data in users_db.items():
            if user_data.get("role") == "student":
                students.append({
                    "userId": user_id,
                    "profile": {
                        "name": {"fullName": user_data.get("name")},
                        "emailAddress": user_data.get("email")
                    }
                })
        
        return {"students": students}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get students: {str(e)}")

@router.get("/courses/{course_id}/students")
async def get_course_students(
    course_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get students in a course"""
    try:
        # Get all students from users_db instead of mock data
        students = []
        for user_id, user_data in users_db.items():
            if user_data.get("role") == "student":
                students.append({
                    "userId": user_id,
                    "profile": {
                        "name": {"fullName": user_data.get("name")},
                        "emailAddress": user_data.get("email")
                    }
                })
        
        return {"students": students}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get students: {str(e)}")

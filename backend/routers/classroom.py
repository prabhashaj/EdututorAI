# backend/routers/classroom.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
import json

from services.classroom_service import ClassroomService
from routers.auth import get_current_user
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

@router.get("/courses/{course_id}/students")
async def get_course_students(
    course_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get students in a course"""
    try:
        # Mock student data
        mock_students = [
            {
                "userId": "student_1",
                "profile": {
                    "name": {"fullName": "Alice Johnson"},
                    "emailAddress": "alice@example.com"
                }
            },
            {
                "userId": "student_2",
                "profile": {
                    "name": {"fullName": "Bob Smith"},
                    "emailAddress": "bob@example.com"
                }
            }
        ]
        
        return {"students": mock_students}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get students: {str(e)}")

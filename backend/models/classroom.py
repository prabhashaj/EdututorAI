# backend/models/classroom.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Course(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    enrollment_code: Optional[str] = None
    course_state: str = "ACTIVE"
    creation_time: Optional[datetime] = None
    teacher_id: Optional[str] = None

class Student(BaseModel):
    user_id: str
    course_id: str
    full_name: str
    email: str
    enrollment_date: Optional[datetime] = None

class CourseWork(BaseModel):
    id: str
    course_id: str
    title: str
    description: Optional[str] = None
    state: str = "PUBLISHED"
    creation_time: Optional[datetime] = None
    due_date: Optional[datetime] = None

class ClassroomSync(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    user_id: str

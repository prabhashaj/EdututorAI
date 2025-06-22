# backend/models/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    EDUCATOR = "educator"

class User(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    name: str
    role: UserRole
    google_id: Optional[str] = None
    courses: Optional[List[str]] = []

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    role: UserRole
    password: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

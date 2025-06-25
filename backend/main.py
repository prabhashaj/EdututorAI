# backend/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
from routers import auth, quiz, classroom
from utils.config import settings

app = FastAPI(
    title="EduTutor AI API",
    description="AI-powered personalized education platform",
    version="1.0.0"
)

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(classroom.router, prefix="/api/classroom", tags=["classroom"])

@app.get("/")
async def root():
    return {"message": "EduTutor AI API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Initialize predefined users
def init_predefined_users():
    """Initialize predefined users for the application"""
    from routers.auth import users_db, pwd_context
    
    # Clear any existing users
    users_db.clear()
    
    # Hash passwords for predefined users
    student_password_hash = pwd_context.hash("student123")
    educator_password_hash = pwd_context.hash("educator123")
    
    # Add student user
    users_db["student_id"] = {
        "id": "student_id",
        "email": "student@edututor.ai",
        "name": "Student User",
        "role": "student",
        "hashed_password": student_password_hash
    }
    
    # Add educator user
    users_db["educator_id"] = {
        "id": "educator_id",
        "email": "educator@edututor.ai",
        "name": "Educator User",
        "role": "educator",
        "hashed_password": educator_password_hash
    }
    
    print("Predefined users initialized successfully")
    print(f"DEBUG: users_db now contains {len(users_db)} users")
    for uid, user in users_db.items():
        print(f"DEBUG: User {uid}: {user['email']} with role {user['role']}")

# Initialize users on startup
init_predefined_users()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

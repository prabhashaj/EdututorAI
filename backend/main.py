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
    
    # Add original student user
    users_db["student_id"] = {
        "id": "student_id",
        "email": "student@edututor.ai",
        "name": "Student User",
        "role": "student",
        "hashed_password": student_password_hash
    }
    
    # Add more student users
    students = [
        {"id": "student_alice", "email": "alice.johnson@edututor.ai", "name": "Alice Johnson"},
        {"id": "student_bob", "email": "bob.smith@edututor.ai", "name": "Bob Smith"},
        {"id": "student_carol", "email": "carol.williams@edututor.ai", "name": "Carol Williams"},
        {"id": "student_david", "email": "david.brown@edututor.ai", "name": "David Brown"},
        {"id": "student_emma", "email": "emma.davis@edututor.ai", "name": "Emma Davis"},
        {"id": "student_frank", "email": "frank.miller@edututor.ai", "name": "Frank Miller"},
        {"id": "student_grace", "email": "grace.wilson@edututor.ai", "name": "Grace Wilson"},
        {"id": "student_henry", "email": "henry.moore@edututor.ai", "name": "Henry Moore"},
        {"id": "student_ivy", "email": "ivy.taylor@edututor.ai", "name": "Ivy Taylor"},
        {"id": "student_jack", "email": "jack.anderson@edututor.ai", "name": "Jack Anderson"},
        {"id": "student_kate", "email": "kate.thomas@edututor.ai", "name": "Kate Thomas"},
        {"id": "student_luke", "email": "luke.jackson@edututor.ai", "name": "Luke Jackson"},
        {"id": "student_maria", "email": "maria.white@edututor.ai", "name": "Maria White"},
        {"id": "student_noah", "email": "noah.harris@edututor.ai", "name": "Noah Harris"},
        {"id": "student_olivia", "email": "olivia.martin@edututor.ai", "name": "Olivia Martin"}
    ]
    
    for student in students:
        users_db[student["id"]] = {
            "id": student["id"],
            "email": student["email"],
            "name": student["name"],
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

# Also initialize users in database for persistence
@app.on_event("startup")
async def startup_event():
    """Initialize database users on startup"""
    try:
        # Import database modules directly
        from db import SessionLocal, UserDB, Base, engine
        from routers.auth import users_db
        
        # Ensure database tables are created
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        try:
            # Add all predefined users to the database
            for user_id, user_data in users_db.items():
                # Check if user already exists in database
                existing = db.query(UserDB).filter(UserDB.email == user_data["email"]).first()
                if not existing:
                    db_user = UserDB(
                        id=user_data["id"],
                        email=user_data["email"],
                        name=user_data["name"],
                        role=user_data["role"],
                        hashed_password=user_data["hashed_password"]
                    )
                    db.add(db_user)
            
            db.commit()
            print(f"✅ Database users initialized successfully - {len(users_db)} users")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"⚠️ Could not initialize database users: {e}")
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# backend/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi.responses import JSONResponse

from models.user import User, UserCreate, UserLogin, UserRole
from services.pinecone_service import PineconeService
from utils.config import settings
from db import SessionLocal, UserDB

router = APIRouter()
pinecone_service = PineconeService()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory user storage (will be populated later)
users_db = {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token"""
    user_id = verify_token(token)
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register new user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(UserDB).filter(UserDB.email == user_data.email).first()
        if existing:
            db.close()
            raise HTTPException(status_code=400, detail="Email already registered")
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password) if user_data.password else None
        db_user = UserDB(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            role=user_data.role,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        access_token = create_access_token(data={"sub": user_id})
        user_response = {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "role": db_user.role
        }
        db.close()
        return JSONResponse(
            status_code=201,
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_response
            }
        )
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=dict)
async def login(user_credentials: UserLogin):
    """Login user"""
    try:
        print(f"[DEBUG] Login attempt for: {user_credentials.email}")
        print(f"[DEBUG] users_db has {len(users_db)} users")
        
        # Check predefined users first
        for user_id, user in users_db.items():
            print(f"[DEBUG] Checking against user_id: {user_id}, email: {user['email']}")
            if user["email"] == user_credentials.email:
                # Found matching email in predefined users
                if verify_password(user_credentials.password, user["hashed_password"]):
                    print(f"[DEBUG] Password verification succeeded for predefined user {user['email']}")
                    access_token = create_access_token(data={"sub": user_id})
                    return {
                        "access_token": access_token,
                        "token_type": "bearer",
                        "user": {
                            "id": user_id,
                            "email": user["email"],
                            "name": user["name"],
                            "role": user["role"]
                        }
                    }
                else:
                    print(f"[DEBUG] Password verification failed for predefined user {user['email']}")
                    raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # If not found in predefined users, try database
        db = SessionLocal()
        try:
            db_user = db.query(UserDB).filter(UserDB.email == user_credentials.email).first()
            if not db_user:
                db.close()
                print("[DEBUG] User not found in database.")
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
            print(f"[DEBUG] Found user in database: {db_user.email}")
            if not db_user.hashed_password or not verify_password(user_credentials.password, db_user.hashed_password):
                db.close()
                print(f"[DEBUG] Password verification failed for {db_user.email}")
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
            print(f"[DEBUG] Password verification succeeded for {db_user.email}")
            access_token = create_access_token(data={"sub": db_user.id})
            user_response = {
                "id": db_user.id,
                "email": db_user.email,
                "name": db_user.name,
                "role": db_user.role
            }
            db.close()
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user_response
            }
        finally:
            db.close()
    except Exception as e:
        db.close()
        print(f"[DEBUG] Exception in login: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token endpoint"""
    try:
        # Find user by username (email)
        user = None
        for u in users_db.values():
            if u.email == form_data.username:
                user = u
                break
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user.id})
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {str(e)}")

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.post("/demo-users")
async def create_demo_users():
    """Create demo users for testing"""
    try:
        demo_users = [
            {
                "id": "student_demo",
                "email": "student@demo.com",
                "name": "Demo Student",
                "role": UserRole.STUDENT
            },
            {
                "id": "educator_demo",
                "email": "educator@demo.com",
                "name": "Demo Educator",
                "role": UserRole.EDUCATOR
            }
        ]
        
        for user_data in demo_users:
            user = User(**user_data)
            users_db[user.id] = user
            await pinecone_service.store_user_profile(user.id, user.dict())
        
        return {"message": "Demo users created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create demo users: {str(e)}")

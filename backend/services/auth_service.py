# backend/services/auth_service.py
from typing import Optional, Dict
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from utils.config import settings

class AuthService:
    """Authentication service for handling user auth operations"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    def decode_google_token(self, token: str) -> Optional[Dict]:
        """Decode Google OAuth token (simplified)"""
        try:
            # In production, verify with Google's public keys
            # For demo, return mock user info
            return {
                "sub": "google_user_123",
                "email": "user@gmail.com",
                "name": "Google User",
                "picture": "https://example.com/avatar.jpg"
            }
        except Exception:
            return None

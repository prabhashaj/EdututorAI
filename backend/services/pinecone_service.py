# backend/services/pinecone_service.py
from pinecone import Pinecone, ServerlessSpec
import json
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
from utils.config import settings

class PineconeService:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)

    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        try:
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            if self.index_name not in existing_indexes:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,  # Using sentence-transformers dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
        except Exception as e:
            print(f"Error creating index: {e}")

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate simple hash-based embedding for demo purposes"""
        # In production, use proper embedding models like sentence-transformers
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert hex to numbers and normalize to create a 384-dimensional vector
        embedding = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0  # Normalize to 0-1
            embedding.extend([val] * 12)  # Repeat to get 384 dimensions
        
        # Ensure exactly 384 dimensions
        while len(embedding) < 384:
            embedding.append(0.0)
        embedding = embedding[:384]
        
        return embedding

    async def store_user_profile(self, user_id: str, user_data: Dict):
        """Store user profile with embedding"""
        try:
            profile_text = f"{user_data.get('name', '')} {user_data.get('role', '')} {' '.join(user_data.get('courses', []))}"
            embedding = self._generate_embedding(profile_text)
            
            metadata = {
                "user_id": user_id,
                "name": user_data.get('name', ''),
                "role": user_data.get('role', ''),
                "email": user_data.get('email', ''),
                "courses": json.dumps(user_data.get('courses', [])),
                "created_at": datetime.now().isoformat()
            }
            
            self.index.upsert([
                (f"user_{user_id}", embedding, metadata)
            ])
            
        except Exception as e:
            print(f"Error storing user profile: {e}")

    async def store_quiz_result(self, user_id: str, quiz_data: Dict, result_data: Dict):
        """Store quiz result with metadata"""
        try:
            quiz_text = f"{quiz_data.get('topic', '')} difficulty_{quiz_data.get('difficulty', 1)}"
            embedding = self._generate_embedding(quiz_text)
            
            result_id = f"quiz_{user_id}_{datetime.now().timestamp()}"
            
            metadata = {
                "user_id": user_id,
                "quiz_id": quiz_data.get('id', ''),
                "topic": quiz_data.get('topic', ''),
                "difficulty": quiz_data.get('difficulty', 1),
                "score": result_data.get('score', 0),
                "total_questions": result_data.get('total_questions', 0),
                "correct_answers": result_data.get('correct_answers', 0),
                "submitted_at": datetime.now().isoformat(),
                "type": "quiz_result"
            }
            
            self.index.upsert([
                (result_id, embedding, metadata)
            ])
            
        except Exception as e:
            print(f"Error storing quiz result: {e}")

    async def get_user_quiz_history(self, user_id: str) -> List[Dict]:
        """Get quiz history for a user"""
        try:
            # Query for user's quiz results
            query_response = self.index.query(
                vector=[0.0] * 384,  # Dummy vector for metadata filtering
                filter={
                    "user_id": {"$eq": user_id},
                    "type": {"$eq": "quiz_result"}
                },
                top_k=100,
                include_metadata=True
            )
            
            history = []
            for match in query_response.matches:
                metadata = match.metadata
                history.append({
                    "topic": metadata.get('topic'),
                    "difficulty": metadata.get('difficulty'),
                    "score": metadata.get('score'),
                    "total_questions": metadata.get('total_questions'),
                    "correct_answers": metadata.get('correct_answers'),
                    "submitted_at": metadata.get('submitted_at')
                })
            
            return sorted(history, key=lambda x: x['submitted_at'], reverse=True)
            
        except Exception as e:
            print(f"Error getting quiz history: {e}")
            return []

    async def get_all_students_data(self) -> List[Dict]:
        """Get all students' data for educator dashboard"""
        try:
            # Query for all student profiles
            query_response = self.index.query(
                vector=[0.0] * 384,
                filter={"role": {"$eq": "student"}},
                top_k=1000,
                include_metadata=True
            )
            
            students_data = []
            for match in query_response.matches:
                metadata = match.metadata
                user_id = metadata.get('user_id')
                
                # Get quiz history for this student
                quiz_history = await self.get_user_quiz_history(user_id)
                
                students_data.append({
                    "user_id": user_id,
                    "name": metadata.get('name'),
                    "email": metadata.get('email'),
                    "courses": json.loads(metadata.get('courses', '[]')),
                    "quiz_history": quiz_history,
                    "total_quizzes": len(quiz_history),
                    "average_score": sum([q['score'] for q in quiz_history]) / len(quiz_history) if quiz_history else 0
                })
            
            return students_data
            
        except Exception as e:
            print(f"Error getting students data: {e}")
            return []

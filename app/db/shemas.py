from pydantic import BaseModel, Field
from datetime import datetime, timezone
from bson import ObjectId

class User(BaseModel):
    username: str
    email: str
    hashed_password: str
    role: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)

class UserProfile(BaseModel):
    first_name: str
    last_name: str
    thread_ids: list[str] = []
    courses: list[str] = []
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    user_id: str

class RefreshToken(BaseModel):
    user_id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    token: str
    created_at: datetime = datetime.now(timezone.utc)
    expires_at: datetime
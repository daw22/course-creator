from pydantic import BaseModel
from datetime import datetime, timezone

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
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, Request
from app.db.connection import db
from app.db.shemas import UserProfile
import jwt
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        # return the userprofile from db
        user_profile = db.user_profiles.find_one({"user_id": user_id}, { "_id": 0 })
        if user_profile is None:
            raise HTTPException(status_code=404, detail="User not found")
        request.state.user = UserProfile(**user_profile)
        return request.state.user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

from fastapi import APIRouter, Depends, HTTPException, Response
import jwt
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import os
from pydantic import BaseModel
from app.db.shemas import User
from app.db.connection import db
from fastapi.security import OAuth2PasswordRequestForm

passwored_hasher = PasswordHash.recommended()
ALGORITHM = "HS256"

class SignupData(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

router = APIRouter(
    prefix="/auth", 
    tags=["auth"],
)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv("JWT_SECRET"), algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/signup")
async def signup(data: SignupData):
    # Check if user already exists
    existing_user = db.users.find_one({"username": data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    existing_email = db.users.find_one({"email": data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password
    hashed_password = passwored_hasher.hash(data.password)
    
    # Create new user
    new_user = {
        "username": data.username,
        "email": data.email,
        "hashed_password": hashed_password,
    }
    
    result = db.users.insert_one(new_user)

    user_profile = {
        "first_name": data.first_name,
        "last_name": data.last_name,
        "thread_ids": [],
        "courses": []
    }
    new_profile = db.user_profiles.insert_one({**user_profile, "user_id": str(result.inserted_id)})
    if not result.acknowledged:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return {"message": "User created successfully"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.users.find_one({"username": form_data.username})
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    if not passwored_hasher.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
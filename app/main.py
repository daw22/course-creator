from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes.auth import router as auth_router
from app.routes.graph import graph_app
from app.routes.courses import courses_router
import os
from pymongo import MongoClient
load_dotenv()


app = FastAPI()
# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ai-course-creator-e3lc.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#db instance
client = MongoClient(os.getenv("DB_URI"))
db = client["course_creator"]

app.include_router(auth_router)
app.include_router(graph_app)
app.include_router(courses_router)


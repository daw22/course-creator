from bson import ObjectId
from app.dependencies import get_current_user
from app.db.connection import db
from fastapi import APIRouter, HTTPException, Depends, Request
from app.db.shemas import Course

courses_router = APIRouter(prefix="/courses", tags=["courses"], dependencies=[Depends(get_current_user)])

@courses_router.get("/my_courses")
async def get_my_courses(request: Request):
    user = request.state.user
    cursor = db.courses.find({"user_id": ObjectId(user.id)})
    # print("Courses found:", list(courses))
    # print("Courses found:", list(courses))
    # courses = [Course(**course) for course in cursor]
    courses = []
    for course in cursor:
        course["user_id"] = str(course["user_id"])
        course["_id"] = str(course["_id"])
        del course["outline"]
        courses.append(course)
    return {"courses": courses}
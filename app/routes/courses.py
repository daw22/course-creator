from bson import ObjectId
from app.dependencies import get_current_user
from app.db.connection import db
from fastapi import APIRouter, HTTPException, Depends, Request
from app.db.shemas import Course
from pydantic import BaseModel
from typing import List
from prerequisite_analyzer.agent import app as graph

courses_router = APIRouter(prefix="/courses", tags=["courses"], dependencies=[Depends(get_current_user)])

class CourseListResponse(BaseModel):
    courses: List[Course]

@courses_router.get("/my_courses", response_model=CourseListResponse)
async def get_my_courses(request: Request):
    user = request.state.user
    cursor = db.courses.find({"user_id": ObjectId(user.id)})
    courses = []
    for course in cursor:
        course["user_id"] = str(course["user_id"])
        course["_id"] = str(course["_id"])
        del course["outline"]
        courses.append(course)
    return {"courses": courses}

@courses_router.get("/{course_id}", response_model=Course)
async def get_course(course_id: str, request: Request):
    user = request.state.user
    course = db.courses.find_one({"_id": ObjectId(course_id), "user_id": ObjectId(user.id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course["user_id"] = str(course["user_id"])
    course["_id"] = str(course["_id"])
    return course

@courses_router.get("/by_thread/{thread_id}", response_model=Course)
async def get_course_by_thread(thread_id: str, request: Request):
    user = request.state.user
    course = db.courses.find_one({"thread_id": thread_id, "user_id": ObjectId(user.id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course["user_id"] = str(course["user_id"])
    course["_id"] = str(course["_id"])
    return course

@courses_router.delete("/{course_id}")
async def delete_course(course_id: str, request: Request):
    user = request.state.user
    print("User ID:", user.id)
    course = db.courses.find_one({"_id": ObjectId(course_id), "user_id": ObjectId(user.id)})
    thread_id = course.get("thread_id", None)
    print("Thread ID:", thread_id)
    #remove thread_from user profile
    if thread_id:
        db.user_profiles.update_one({"_id": ObjectId(user.id)}, {"$pull": {"thread_ids": thread_id}})
    #delete the course
    dcourse = db.courses.delete_one({"_id": ObjectId(course_id), "user_id": ObjectId(user.id)})
    # Also delete related chapters and subtopics
    chapters = db.chapters.find({"course_id": course_id})
    chapter_ids = [str(chapter["_id"]) for chapter in chapters]
    db.chapters.delete_many({"course_id": course_id})
    db.subtopics.delete_many({"chapter_id": {"$in": chapter_ids}})
    if dcourse.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Problem in deleting course or related content")
    return {"detail": "Course and related content deleted successfully"}

@courses_router.get("/get_generated_content/{course_id}")
async def get_generated_content(course_id: str):
    chapters_cursor = db.chapters.find({"course_id": course_id}).sort("order", 1)
    course_content = []
    for chapter in chapters_cursor:
        subtopics_cursor = db.subtopics.find({"chapter_id": str(chapter["_id"])}).sort("order", 1)
        subtopics = []
        for subtopic in subtopics_cursor:
            subtopics.append({
                "title": subtopic["title"],
                "content": subtopic["content"],
                "target": subtopic["target"],
                "summary": subtopic.get("summary", ""),
                "order": subtopic["order"]
            })
        course_content.append({
            "chapter_title": chapter["title"],
            "chapter_target": chapter["target"],
            "chapter_order": chapter["order"],
            "subtopics": subtopics,
            "quiz": chapter.get("quiz", None)
        })
    # also get the last checkpoint id from checkpointer
    course_thread_id = db.courses.find_one({"_id": ObjectId(course_id)})["thread_id"]
    config = {"configurable": {"thread_id": course_thread_id}}
    snapshots = list(graph.get_state_history(config))
    last_checkpoint = None
    if snapshots and len(snapshots) > 0:
        last_checkpoint = snapshots[0].config["configurable"].get("checkpoint_id", None)
    return {"course_content": course_content, "last_checkpoint": last_checkpoint}
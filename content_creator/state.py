from pydantic import BaseModel
from typing import Optional


class TopicState(BaseModel):
    course_id: str
    chapter_id: Optional[str] = None
    course_title: Optional[str] = None
    course_target: Optional[str] = None
    chapter_title: Optional[str] = None
    chapter_target: Optional[str] = None
    topic_title: Optional[str] = None
    topic_target: Optional[str] = None
    generated_content: Optional[str] = None
    content_summary: Optional[str] = None
    questions: list[str] = []
    course_progress: list[int] = [0, 0]  # give default
    quiz: list = []
    quiz_answers: list[int] = []
    quiz_results: list[int] = []
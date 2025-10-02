from pydantic import BaseModel


class TopicState(BaseModel):
    course_id: str
    chapter_id: str
    course_title: str
    course_target: str
    chapter_title: str 
    chapter_target: str
    topic_title: str
    topic_target: str
    generated_content: str
    content_summary: str
    questions: list[str] = []
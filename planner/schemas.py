from pydantic import BaseModel, Field
from typing import Optional, List


class subtopic(BaseModel):
    """A specific sub-topic or lesson within a chapter."""
    subtopic_title: str = Field(description="The title of the subtopic")
    subtopic_target: Optional[str] = Field(description="The target of the subtopic")

class Chapter(BaseModel):
    """A major section of the course, typically covering a broad topic."""
    chapter_title: str
    chapter_target: Optional[str] = Field(description="The target of the chapter")
    subtopics: List[subtopic] = Field(description="A list of subtopics in the chapter")

class CoursePlan(BaseModel):
    """
    A tool to generate a detailed, structured course plan or outline,
    organized into chapters and sub-topics.
    """ 
    chapters: List[Chapter] = Field(description="A list of chapters in the course")

class Targets(BaseModel):
    """Use this to create sub targets for a course, each target should one or two sentences long"""
    targets: List[str] = Field(description="A list of sub targets for the course")
from pydantic import BaseModel, Field
from typing import Optional, List


class subtopic(BaseModel):
    """A specific sub-topic or lesson within a chapter."""
    subtopic_title: str = Field(description="The title of the subtopic")
    subtopic_target: Optional[str] = Field(description="The target of the subtopic")

class Chapter(BaseModel):
    """A major section of the course, typically covering a broad topic."""
    chapter_title: str = Field(description="The title of the chapter, a short phrase describing the chapter")
    chapter_target: Optional[str] = Field(description="The target of the chapter")
    chapter_number: int = Field(description="The order of the chapter in the course, the first chapter should be 1")
    number_of_subtopics: int = Field(description="The number of subtopics in the chapter")
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
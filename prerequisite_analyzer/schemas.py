from typing import Literal, List, Optional
from pydantic import BaseModel, Field

# output schema
class Recommendation(BaseModel):
  level: Literal[
    "Full foundational introduction",
    "Targeted refresher", 
    "Brief Review", 
    "Assume as Prerequisite"] = Field(description="based on the user answer")
  justification: str = Field(description="why you pick the level")

class Prerequisite(BaseModel):
  domain: str = Field(description="domain of the question for this prerequisite")
  user_assessment: str = Field(description="user's answer for the question based on this prerequisite")
  recommendation: Recommendation

class CurriculumPrerequisiteAnalysis(BaseModel):
  """Call this tool to provide your final, analysis of the user's proficiency on the course prerequisites."""
  course_subject: str = Field(description="course_title")
  user_knowledge_summary: str = Field(description="summary of the user's knowledge on the prerequesites")
  prerequisites: List[Prerequisite]


# prerequisite list output tool
class PrerequisitesList(BaseModel):
  """Use this tool to provide a list of prerequisites"""
  prerequisites: List[str] = Field(description="list of prerequisites")

# questions list output tool
class QuestionsList(BaseModel):
  """Use this tool to provide a list of questions"""
  questions: List[str] = Field(description="list of questions")

#queston or course title
class QuestionOrTitle(BaseModel):
  """use this tool to provide the course title or to ask the user more question(to help identify what they want to learn about)"""
  course_title: Optional[str] = Field(description="a course title, if you are confident about what the want to learn about")
  question: Optional[str] = Field(description="a question to ask the user to better understand what they want to learn about")


class CourseTargetSuggestion(BaseModel):
  """Use this tool to suggest an overall target for a course based on its title and the user's proficiency in its prerequisites."""
  targets: List[str] = Field(description="a collection of realistic and achievable overall targets for the course that aligns with both the course content and the user's current knowledge.")
  suggested_target: int = Field(description="which target is more suitable for the user based on their proficiency in the prerequisites.")
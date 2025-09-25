from pydantic import BaseModel
from prerequisite_analyzer.schemas import CurriculumPrerequisiteAnalysis
from typing import List
from planner.schemas import CoursePlan

class PlannerState(BaseModel):
    course_titile: str
    learnning_target: str
    user_profficency: CurriculumPrerequisiteAnalysis
    targets_chapter: List[str] = []
    course_outline: CoursePlan = None
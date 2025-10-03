from prerequisite_analyzer.schemas import CurriculumPrerequisiteAnalysis, QuestionOrTitle, CourseTargetSuggestion
from langgraph.graph import MessagesState
from typing import Optional, List
from planner.schemas import CoursePlan

class AgentState(MessagesState):
  prerequisites: List[str]
  questions: List[str]
  answers: List[str]
  course_title: Optional[str]
  qort: QuestionOrTitle
  custom_request: Optional[str]
  output: CurriculumPrerequisiteAnalysis # the final json output
  course_target_suggestion: CourseTargetSuggestion # the course target suggestion output
  course_target: int
  course_outline: CoursePlan | None # course outline
  course_progress: list[int] = [0, 0] # [current chapter index, current topic index]
  course_id: str
  user_id: str
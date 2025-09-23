from prerequisite_analyzer.schemas import CurriculumPrerequisiteAnalysis, QuestionOrTitle, CourseTargetSuggestion
from langgraph.graph import MessagesState
from typing import Annotated, Optional, List
import operator

class AgentState(MessagesState):
  prerequisites: List[str]
  questions: List[str]
  answers: List[str]
  course_title: Optional[str]
  qort: QuestionOrTitle
  custom_request: Optional[str]
  output: CurriculumPrerequisiteAnalysis # the final json output
  course_target_suggestion: CourseTargetSuggestion # the course target suggestion output
  course_target: Optional[int] # index to track which course target suggestion the user picked

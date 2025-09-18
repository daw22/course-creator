from prerequisite_analyzer.schemas import CurriculumPrerequisiteAnalysis, QuestionOrTitle
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

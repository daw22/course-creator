from pydantic import BaseModel, Field


class Question(BaseModel):
    question: str = Field(..., description="The question text")
    answer: int
    choices: list[str]

class SummaryAndQuestions(BaseModel):
    """Use this tool to create summary and questions for the subtopic."""
    summary: str = Field(..., description="A bulleted summary of the content")
    questions: list[Question] = Field(..., description="A list of questions related to the content")
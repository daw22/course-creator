from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from content_creator.state import TopicState
from content_creator.schemas import SummaryAndQuestions
from app.db.shemas import Course
from app.db.connection import db
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=1)

"""
Things to do
============
1. generate a markup for the topic -- inputs -> course title, course target, chapter title,
 chapter target, topic title, topic target, title of previous topic and summary of previous topic
2. generate a summary for the topic (bullated points)
3. generate questions for the topic (1 to 3 max choice questions)
4. store the generated content along with the summary and questions in the database
5. also store the generated content to a vector database
6. at the end of a chapter, generate a summary for the chapter
7. at the end of the chapter test the user with the questions generated for each topic in the chapter
8. store the test result
9. update course progress
"""

def generate_content(state: TopicState):
  sys_msg = f"""You are an assistant for a course creator.  
  Your role is to generate detailed content for a specific topic within a chapter of a course.  
  You will be provided with
    - the course title 
    - the course target
    - the chapter title (where the topic is located)
    - the chapter target (the target of the chapter, i.e. the topic you are working on is part of this chapter)
    - the topic title (the specific subject matter to be covered)
    - the topic target (the target of the topic, i.e. what the learner should achieve after completing the topic)
  Rules:
  - Content must be in markdown format. !! ALWAYS use markdown format !! don't add anything outside markdown format.
  - The content should be comprehensive and achive the topic target.
  - Do not include any introductory or concluding remarks.
  - Ensure the content is appropriate for the specified target audience.
  - Use clear and concise language.
  - Provide relevant examples to illustrate key points.
  - Maintain a logical flow of information.
  - Include headings and subheadings as necessary to organize the content.

    Here is the information you need to generate the content:
    - Course Title: {state.course_title}
    - Course Target: {state.course_target}
    - Chapter Title: {state.chapter_title}
    - Chapter Target: {state.chapter_target}
    - Topic Title: {state.topic_title}
    - Topic Target: {state.topic_target}
  """

  response = llm.invoke([SystemMessage(content=sys_msg)] + [HumanMessage(content="Generate the content now.")])
  return {"generated_content": response.content}

def summary_and_questions(state: TopicState):
  sys_msg = f"""You are an assistant for a course creator.  
  Your role is to create a bulleted summary and questions for a specific topic within a chapter of a course.  
  You will be provided with
    - the topic title (the specific subject matter to be covered)
    - the topic target (the target of the topic, i.e. what the learner should achieve after completing the topic)
    - the generated content for the topic
  Instructions:
  - Create a concise bulleted summary that captures the key points of the content.
  - Develop 1 to 3 multiple-choice questions that test understanding of the content.
  - Each question should have one correct answer and three plausible distractors.
  - Ensure that questions are clear and directly related to the content.
  Finally, format your response using the SummaryAndQuestions schema.

    Here is the information you need to create the summary and questions:
    - Topic Title: {state.topic_title}
    - Topic Target: {state.topic_target}
    - Generated Content: {state.generated_content}
  """
  llm_with_tool = llm.bind_tools([SummaryAndQuestions])
  response = llm_with_tool.invoke([SystemMessage(content=sys_msg), HumanMessage(content="Create the summary and questions now.")])
  result = getattr(response, "parsed_output", None)
  if result:
    return {
      "content_summary": result.summary,
      "questions": [q.model_dump() for q in result.questions]
    }
  else:
    return {
      "content_summary": "",
      "questions": []
    }
  
def chapter_router(state: TopicState):
  #check if this is the last topic in the chapter
  chapter = db.chapters.find_one({"_id": state.chapter_id})
  if chapter is None:
    return "create_chapter_record"
  if chapter["number_of_subtopics"] == chapter["course_progress"][1] + 1:
    return "create_chapter_summary"
  else:
    return "update_chapter_record"
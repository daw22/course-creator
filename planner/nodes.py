from planner.state import PlannerState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from dotenv import load_dotenv

from planner.schemas import Targets, CoursePlan
load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=1)

def sub_target_creator(state: PlannerState):
  sys_msg = """You are an assistant for a course creator agent.
  Your role is to creates sub targets for a course based on the user's learning target and proficiency.
  The subtargets should cover from the user's current proficiency to the learning target.
  You will be privided with course title, learning target and user proficiency.
  Responsibilities:
    - Create sub targets that will help the user reach their learning target.
    - Always make the first target where the users prerequisite deficiencies will be addressed and an introduction to the course.
    - each subtarget you created will be used to create a chapter in the course.
    - Make sure the subtargets are in a logical order.
  Final Output:
    - Return a list of sub targets using the Targets tool.

  course title: {course_title}
  learning target: {learning_target}
  user proficiency: {user_proficiency}
  """
  llm_with_tool = llm.bind_tools([Targets])
  response = llm_with_tool.invoke([SystemMessage(content=sys_msg.format(
    course_title=state.course_titile,
    learning_target=state.learnning_target,
    user_proficiency=state.user_profficency.json()
  ))] + [HumanMessage(content="Create sub targets for the course")])

  tool_calls = getattr(response, "tool_calls", [])
  if tool_calls:
    args = tool_calls[0]["args"]
    return {"targets_chapter": args["targets"]}
  return {"targets_chapter": []}

def course_outline_creator(state: PlannerState):
  sys_msg = f"""You are an assistant for a course creator agent.
  Your role is to create a course outline based on the course title, learning target, and sub targets.
  You will be provided with the course title, learning target, and sub targets.
  Responsibilities:
    - Create a course outline that will help the user reach their learning target.
    - Each chapter in the course outline should have a title and a list of subtopics.
    - use the sub targets to create chapters
    - Make sure the chapters and subtopics are in a logical order.
    - also specify the target of each sub topic you create with one or two sentences
  Final Output:
    - Return a course outline using the CoursePlan tool.
    
    course_title = {state.course_titile}
    learnning target = {state.learnning_target}
    sub targets = {state.targets_chapter}
    """
  
  llm_with_tool = llm.bind_tools([CoursePlan])
  response = llm_with_tool.invoke([SystemMessage(content=sys_msg)] + [HumanMessage(content="Create a course outline for the course")])

  tool_calls = getattr(response, "tool_calls", [])
  if tool_calls:
    args = tool_calls[0]["args"]
    return {"course_outline": args["chapters"]}
  return {"course_outline": None}

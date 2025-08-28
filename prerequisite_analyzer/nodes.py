from prerequisite_analyzer.state import AgentState
from prerequisite_analyzer.schemas import PrerequisitesList, QuestionsList, QuestionOrTitle
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.types import interrupt
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=1)

def course_title_extractor(state: AgentState):
  sys_msg = """You are an assistant for a course creator agent.
  Your role is to determine what the user wants to learn about from the conversation below.  

  Instructions:
  - If you clearly know the course title → return it.  
  - If you don’t have enough info → ask a clarifying question instead.  
  - Always output in this format using the QuestionOrTitle tool:  

  QuestionOrTitle:
    course_title: [course name OR None]  
    question: [clarifying question OR None]  

  Rules:  
  - Only one of course_title or question should have a value (the other must be None).  
  - If the user’s request is too broad (e.g. “programming”), ask a narrowing question (e.g. “What programming language?” or “Introductory or advanced?”).  
  - If the conversation already has 5 back-and-forths, stop asking further questions and return your best guess for the course title.  
  - Keep course titles concise (e.g. “Introduction to Python Programming”, not long sentences).
  Conversation:  
  """
  llm_with_tool = llm.bind_tools([QuestionOrTitle])
  response = llm_with_tool.invoke([SystemMessage(content=sys_msg)] + state["messages"])
  tool_calls = getattr(response, "tool_calls", [])
  if tool_calls:
    args = tool_calls[0]["args"]
    course_title = args["course_title"]
    if course_title:
      return {"qort": args, "course_title": course_title}
    else:
      return {"qort": args, "messages": [AIMessage(content=args["question"])]}
  return {"qort": None}

def route_title_identifier(state: AgentState):
  qort = state["qort"]
  if qort["course_title"]:
    return "get_prerequisites"
  if qort["question"]:
    return "course_title_response"
  return "course_title_extractor"

def course_title_response(state: AgentState):
  question = state["qort"]["question"]
  answer = interrupt(question)
  return {"messages": [HumanMessage(content=answer)]}

def get_prerequisites(state: AgentState):
  sys_prompt = """ You are an assistant for a course creator.  
  Your role is to identify the prerequisites of a course.  

  Instructions:  
  - Identify at most 5 prerequisites for the given course title (it can be fewer).  
  - Never list more than 5 prerequisites. If there are more, combine or summarize them so the total is still 5 or fewer.  
  - Each prerequisite should include relevant sub-topics related to the course.  
    Example: 
      courese_title: Digital signal Analysis
      prerequisites: 
        1 - Maths, linear algebra, calculus, basic trignonometry
        2 - signal and systems, Fourier analysis
        3 - programming, Gnu Octave
        4 - basic electronics, python, basic programming concepts
  Finaly: use the PrerequisitesList tool to format your answer
  """
  llm_with_tool = llm.bind_tools([PrerequisitesList])
  message = f"Identify the prerequisites for this course: {state["course_title"]}"
  response = llm_with_tool.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=message)])
  return {"prerequisites": response.tool_calls[0]["args"]["prerequisites"]}

def prepare_questions(state: AgentState):
  sys_prompt = """ You are an assistant for a course creator agent, given a list of prerequisites for a course your job is 
  to preprare a question for every prerequesite
  - The aim of every question is to identify the students proficiency on the given topic
  - Prepare the questions in a way the student can answer like 'need a refresher', 'no experience', 'no refresher needed'
  (multiple choise type question) but donot mention how the student should answer
  - The questions should not be to long, maximum of two sentences and 20 words long.
  Finaly: use the QuestionsList tool to format your answer  
  """
  llm_with_tools = llm.bind_tools([QuestionsList])
  prerequisites_formated = [f"- {prerequisite}\n" for prerequisite in state["prerequisites"]]
  message = f"prepare questions for this prerequesites: \n {prerequisites_formated}"
  response = llm_with_tools.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=message)])
  return {"questions": response.tool_calls[0]["args"]["questions"]}

def get_answer(state: AgentState):
  answers = interrupt("Answer the questions please.")
  if isinstance(answers, list):
    return {"answers": answers}
  
def route_human_input(state: AgentState):
  answers = state['answers']
  questions = state['questions']
  print(f"questions len: {len(questions)} ** answers len: {len(answers)}")
  if len(answers) == len(questions):
    return "__end__"
  else:
    return "get_answers"
from prerequisite_analyzer.state import AgentState
from prerequisite_analyzer.schemas import PrerequisitesList, QuestionsList, QuestionOrTitle, CurriculumPrerequisiteAnalysis, CourseTargetSuggestion
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
  - If the user’s request is too broad (e.g. “programming”), ask a narrowing question 
  (e.g. “What programming language?” or “Introductory or advanced?”).  
  - keep asking the user questions until you have enough to get a reasonably narrow topic 
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
  if qort["course_title"] and not qort["question"]:
    return "get_prerequisites"
  else:
    return "course_title_response"

def course_title_response(state: AgentState):
  return {}

def get_prerequisites(state: AgentState):
  sys_prompt = """ You are an assistant for a course creator.  
  Your role is to identify the prerequisites of a course.  

  Instructions:  
  - Identify at most 5 prerequisites for the given course title (it can be fewer).  
  - Never list more than 5 prerequisites. If there are more, combine or summarize them so the total is still 5.  
  - Each prerequisite should include relevant sub-topics related to the prerequisite.
    Example: 
      courese_title: Digital signal Analysis
      prerequisites: 
        1 - Maths, linear algebra, calculus, basic trignonometry
        2 - signal and systems, Fourier analysis
        3 - programming, python, basic programming concepts
        4 - basic electronics, Gnu Octave
  Rules:
  - don't include more than 5 prerequisites
  - Don't include broad prerequisites (like mathematics, programming, physics ...)
  - Don't include soft skills as a prerequisite (like communication skill, teamwork skill ...)
  - Don't include general skills as a prerequisite (like problem solving skill, critical thinking, basic computer skills ...)
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
  - Prepare the questions in a way the student can answer like 'need a refresher', 'no experience', 'comfortable'
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
  return {}
  
def route_human_input(state: AgentState):
  answers = state['answers']
  questions = state['questions']
  print(f"questions len: {len(questions)} ** answers len: {len(answers)}")
  if answers and len(answers) == len(questions):
    return "final_response"
  else:
    return "get_answer"
  
def final_response(state: AgentState):
  sys_prompt = """You are an asistant for a course creator agent
  Your goal is to create summary of user's proficeincy in prerequsites of a course
  You will be give the following informations
  - the course title
  - the prerequesites of the course
  - the questions asked to the user about the prerequisites alog with the answers from the user
  Using this information and the CurriculumPrerequisiteAnalysis tool return your analysis
  """
  prerequisites_formated = [f"- {prerequisite}\n" for prerequisite in state["prerequisites"]]
  qa_formated = [f"question: {question}\nanswer: {answer}" for question, answer in zip(state["questions"], state["answers"])]
  message = f""" coures title: {state["course_title"]}
  prerequsites:\n{prerequisites_formated}
  questions:\n{qa_formated}
  """
  llm_with_tool = llm.bind_tools([CurriculumPrerequisiteAnalysis])
  response = llm_with_tool.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=message)])
  tool_calls = getattr(response, "tool_calls", [])
  if tool_calls:
    args = tool_calls[0]["args"]
    return {"output": args}
  else:
    return {"output": None}
  
def suggest_course_target(state: AgentState):
    sys_prompt = """ You are an assistant for a course creator agent
    Your role is to suggest an overall target for a course based on its title and the user's proficiency in its prerequisites.
    
    You are expected to:
    - Analyze the course title to understand its scope and objectives.
    - Review the user's proficiency levels in the identified prerequisites.
    - Suggest realistic and achievable overall targets for the course that aligns with both the course content and the user's current knowledge that the user can choose from.
    - sugget which target is more suitable for the user based on their proficiency in the prerequisites.
    Use the CourseTargetSuggestion tool to format your response.
    """
    llm_with_tool = llm.bind_tools([CourseTargetSuggestion])
    message = f"Course Title: {state['course_title']}\nUser Proficiency Summary: {state['output']['user_knowledge_summary']}"
    response = llm_with_tool.invoke([SystemMessage(content=sys_prompt), HumanMessage(content=message)])
    tool_calls = getattr(response, "tool_calls", [])
    if tool_calls:
      args = tool_calls[0]["args"]
      return {"course_target_suggestion": args}
    else:
      return {"course_target_suggestion": None}
    
def get_course_target(state: AgentState):
    return {}

def route_course_target(state: AgentState):
    target = state["course_target"]
    if target < len(state["course_target_suggestion"]["targets"]):
        return "END"
    else:
        return "get_course_target"
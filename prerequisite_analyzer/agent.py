from langgraph.graph import StateGraph, START, END
from prerequisite_analyzer.state import AgentState
from prerequisite_analyzer.nodes import get_prerequisites, prepare_questions, get_answer, route_human_input, suggest_course_target, planner_app_runner
from prerequisite_analyzer.nodes import course_title_extractor, route_title_identifier, course_title_response, final_response, get_course_target, route_course_target
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.mongodb import MongoDBSaver

from pymongo import MongoClient

db_uri = "mongodb://dawit:dawitxxd@localhost:27017/course_creator?retryWrites=true&w=majority"
client = MongoClient(db_uri)
db = client.get_database()
checkpointer = MongoDBSaver(db)

graph = StateGraph(AgentState)

graph.add_node("course_title_extractor", course_title_extractor)
graph.add_node("route_title_identifier", route_title_identifier)
graph.add_node("course_title_response", course_title_response)
graph.add_node("get_prerequisites", get_prerequisites)
graph.add_node("prepare_questions", prepare_questions)
graph.add_node("get_answer", get_answer)
graph.add_node("route_human_input", route_human_input)
graph.add_node("final_response", final_response)
graph.add_node("suggest_course_target", suggest_course_target)
graph.add_node("get_course_target", get_course_target)
graph.add_node("route_course_target", route_course_target)
graph.add_node("planner_app_runner", planner_app_runner)

graph.add_edge(START, "course_title_extractor")
graph.add_conditional_edges("course_title_extractor", route_title_identifier)
graph.add_edge("course_title_response", "course_title_extractor")
graph.add_edge("get_prerequisites", "prepare_questions")
graph.add_edge("prepare_questions", "get_answer")
graph.add_conditional_edges("get_answer", route_human_input)
graph.add_edge("final_response", "suggest_course_target")
graph.add_edge("suggest_course_target", "get_course_target")
graph.add_conditional_edges("get_course_target", route_course_target)
app = graph.compile(checkpointer=checkpointer, interrupt_before=["course_title_response", "get_answer", "get_course_target"])

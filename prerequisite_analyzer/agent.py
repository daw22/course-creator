from langgraph.graph import StateGraph, END
from prerequisite_analyzer.state import AgentState
from prerequisite_analyzer.nodes import get_prerequisites, prepare_questions, get_answer, route_human_input
from prerequisite_analyzer.nodes import course_title_extractor, route_title_identifier, course_title_response, final_response
from langgraph.checkpoint.memory import MemorySaver

graph = StateGraph(AgentState)

graph.add_node("course_title_extractor", course_title_extractor)
graph.add_node("route_title_identifier", route_title_identifier)
graph.add_node("course_title_response", course_title_response)
graph.add_node("get_prerequisites", get_prerequisites)
graph.add_node("prepare_questions", prepare_questions)
graph.add_node("get_answers", get_answer)
graph.add_node("route_human_input", route_human_input)
graph.add_node("final_response", final_response)

graph.set_entry_point("course_title_extractor")
graph.add_conditional_edges("course_title_extractor", route_title_identifier)
graph.add_edge("course_title_response", "course_title_extractor")
graph.add_edge("get_prerequisites", "prepare_questions")
graph.add_edge("prepare_questions", "get_answers")
graph.add_conditional_edges("get_answers", route_human_input)
app = graph.compile(checkpointer=MemorySaver())

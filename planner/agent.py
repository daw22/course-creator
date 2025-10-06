from langgraph.graph import StateGraph, START, END
from planner.state import PlannerState
from planner.nodes import sub_target_creator, course_outline_creator

graph = StateGraph(PlannerState)
graph.add_node("sub_target_creator", sub_target_creator)
graph.add_node("course_outline_creator", course_outline_creator)
graph.add_edge(START, "sub_target_creator")
graph.add_edge("sub_target_creator", "course_outline_creator")
app = graph.compile()
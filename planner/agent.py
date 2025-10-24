from langgraph.graph import StateGraph, START, END
from planner.state import PlannerState
from planner.nodes import sub_target_creator, course_outline_creator, outline_aproval, outline_router

graph = StateGraph(PlannerState)
graph.add_node("sub_target_creator", sub_target_creator)
graph.add_node("course_outline_creator", course_outline_creator)
graph.add_node("outline_aproval", outline_aproval)
graph.add_node("outline_router", outline_router)
graph.add_edge(START, "sub_target_creator")
graph.add_edge("sub_target_creator", "course_outline_creator")
graph.add_edge("course_outline_creator", "outline_aproval")
graph.add_conditional_edges("outline_aproval", outline_router)
app = graph.compile()
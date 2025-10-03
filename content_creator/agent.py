from content_creator.nodes import generate_content, summary_and_questions, store_content
from content_creator.nodes import chapter_router, create_quiz, quiz_time, quiz_router, store_quiz_result

from content_creator.state import TopicState
from langgraph.graph import StateGraph


content_creator_graph = StateGraph(TopicState)

content_creator_graph.add_node("generate_content", generate_content)
content_creator_graph.add_node("summary_and_questions", summary_and_questions)
content_creator_graph.add_node("store_content", store_content)
content_creator_graph.add_node("chapter_router", chapter_router)
content_creator_graph.add_node("create_quiz", create_quiz)
content_creator_graph.add_node("quiz_time", quiz_time)
content_creator_graph.add_node("quiz_router", quiz_router)
content_creator_graph.add_node("store_quiz_result", store_quiz_result)

content_creator_graph.set_entry_point("generate_content")
content_creator_graph.add_edge("generate_content", "summary_and_questions")
content_creator_graph.add_edge("summary_and_questions", "store_content")
content_creator_graph.add_conditional_edges("store_content", chapter_router)
content_creator_graph.add_edge("create_quiz", "quiz_time")
content_creator_graph.add_edge("quiz_time", "quiz_router")

content_creator_app = content_creator_graph.compile(interrupt_before=["quiz_time"])
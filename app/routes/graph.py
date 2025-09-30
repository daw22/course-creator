from prerequisite_analyzer.agent import app as graph
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import StreamingResponse
from uuid import uuid4
import json
from app.dependencies import get_current_user
from fastapi import Depends, Request

from fastapi import APIRouter, HTTPException

graph_app = APIRouter(prefix="/graph", tags=["graph"], dependencies=[Depends(get_current_user)])

class Answers(BaseModel):
  answers: List[str]
  thread_id: str

class InterruptResume(BaseModel):
  response: str | list[str] | int
  thread_id: str
async def stream_graph(state: Optional[dict], thread_id: Optional[str]):
  if not thread_id:
    thread_id = str(uuid4())
  config = {"configurable": {"thread_id": thread_id}}
  async for chunk in graph.astream_events(state, config, version="v2"):
    data = chunk["data"]
    kind = chunk["event"]
    name = chunk["name"]
    print(chunk, "\n\n")
    current_state = graph.get_state(config)
    print("state: ", current_state, "\n\n")
    if kind == "on_chain_start":
      if name == "LangGraph":
        yield f"{json.dumps({"type": "on_app_start", "thread_id": thread_id})}"
    if kind == "on_chain_end":
      if name == "LangGraph":
        current_state = graph.get_state(config)
        if current_state.next:  
          if current_state.next[0] == "course_title_response":
            yield f"{json.dumps({"type": "on_title_clarification", "thread_id": thread_id, "question": current_state.values["qort"]["question"]})}"
          if current_state.next[0] == "get_answer":
            yield f"{json.dumps({"type": "on_prerequisite_questions", "thread_id": thread_id, "questions": current_state.values["questions"]})}"
          if current_state.next[0] == "get_course_target":
            yield f"{json.dumps({"type": "on_course_target_suggestion", "thread_id": thread_id, "course_target_suggestion": current_state.values["course_target_suggestion"]})}"
        else:
          yield f"{json.dumps({"type": "on_prerequistes_report", "thread_id": thread_id, "course_outline": current_state.values["course_outline"]})}"


@graph_app.get("/start")
async def start(request: Request):
  state = {"messages": [HumanMessage(content=f"Hi there! I am {request.state.user.first_name}")]}
  return StreamingResponse(stream_graph(state=state, thread_id=None), media_type="text/event-stream")

@graph_app.post("/resume")
async def resume(data: InterruptResume):
  user_response = data.response
  config = {"configurable": {"thread_id": data.thread_id}}
  state = graph.get_state(config)
  if state is None:
    raise HTTPException(404, f"thread_id: {data.thread_id} not found!")
  if not state.next:
    raise HTTPException(500, "Operation cannot be resumed")
  if isinstance(user_response, str) and state.next[0] == "course_title_response":
    user_answer = HumanMessage(content=user_response)
    graph.update_state(config, {"messages": [user_answer]})
  elif isinstance(user_response, list) and state.next[0] == "get_answer":
    graph.update_state(config, {"answers": user_response})
  elif isinstance(user_response, int) and state.next[0] == "get_course_target":
    graph.update_state(config, {"course_target": user_response})
  else:
    raise HTTPException(403, "Invalid response type")
  return StreamingResponse(stream_graph(state=None, thread_id=data.thread_id), media_type="text/event-stream")
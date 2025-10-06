from bson import ObjectId
from prerequisite_analyzer.agent import app as graph
from content_creator.agent import content_creator_app
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel
from typing import List, Optional, Any
from fastapi.responses import StreamingResponse
from uuid import uuid4
import json
from app.dependencies import get_current_user
from app.db.connection import db
from fastapi import Depends, Request
from app.db.connection import checkpointer
from fastapi import APIRouter, HTTPException

graph_app = APIRouter(prefix="/graph", tags=["graph"], dependencies=[Depends(get_current_user)])

class Answers(BaseModel):
  answers: List[str] | str
  thread_id: str | None

class InterruptResume(BaseModel):
  response: Any
  thread_id: str
  resume_from: str

async def stream_graph(state: Optional[dict], thread_id: Optional[str], checkpoint_id: Optional[str] = None):
  if not thread_id:
    thread_id = str(uuid4())
  config = {"configurable": {"thread_id": thread_id, "checkpoint_id": checkpoint_id}}
  async for chunk in graph.astream_events(state, config, version="v2"):
    data = chunk["data"]
    kind = chunk["event"]
    name = chunk["name"]
    #print(chunk, "\n\n")
    current_state = graph.get_state(config)
    print("state: ", current_state, "\n\n")
    if kind == "on_chain_start" and not current_state.next:
      if name == "LangGraph":
        yield f"{json.dumps({"type": "on_app_start", "thread_id": thread_id})}"
    if kind == "on_chain_end":
      if name == "LangGraph":
        if current_state.next:  
          if current_state.next[0] == "course_title_response":
            yield f"{json.dumps({"type": "on_title_clarification", "thread_id": thread_id, "question": current_state.values["qort"]["question"]})}"
          if current_state.next[0] == "get_answer":
            yield f"{json.dumps({"type": "on_prerequisite_questions", "thread_id": thread_id, "questions": current_state.values["questions"]})}"
          if current_state.next[0] == "get_course_target":
            yield f"{json.dumps({"type": "on_course_target_suggestion", "thread_id": thread_id, "course_target_suggestion": current_state.values["course_target_suggestion"]})}"
          if current_state.next[0] == "content_creator_pause":
            course_outline = current_state.values.get("course_outline", None)
            course_progress = current_state.values.get("course_progress", [0, 0])
            waiting_for = current_state.values.get("waiting_on", None)
            subtopic_to_generate = course_outline[course_progress[0]]["subtopics"][course_progress[1]]
            yield f"{json.dumps({'type': 'on_content_creation_start', 'thread_id': thread_id, 'subtopic_title': subtopic_to_generate['subtopic_title'], 'subtopic_target': subtopic_to_generate['subtopic_target']})}"
          if current_state.next[0] == "content_creator_runner":
            course_outline = current_state.values.get("course_outline", None)
            course_progress = current_state.values.get("course_progress", [0, 0])
            waiting_for = current_state.values.get("waiting_on", None)
            quiz = current_state.values.get("quiz", [])
            if quiz and waiting_for == "quiz_time":
              yield f"{json.dumps({'type': 'on_quiz_time', 'thread_id': thread_id, 'quiz': quiz})}"
            else:
              subtopic_to_generate = course_outline[course_progress[0]]["subtopics"][course_progress[1]]
              yield f"{json.dumps({'type': 'on_subtopic_generated', 'thread_id': thread_id, 'subtopic_title': subtopic_to_generate['subtopic_title'], 'subtopic_target': subtopic_to_generate['subtopic_target'], 'generated_content': current_state.values.get('generated_content', '')})}"
        else:
          yield f"{json.dumps({"type": "on_course_generation_complete", "thread_id": thread_id})}"


@graph_app.post("/start")
async def start(request: Request, data: Answers):
  state = {"messages": [HumanMessage(content=f"Hi there! I am {request.state.user.first_name}"), 
                        AIMessage(content=f"Hello {request.state.user.first_name}! What do you want to learn about today?"),
                        HumanMessage(content=f"{data.answers}")], 
           "user_id": str(request.state.user.id)}
  #add the thread_id to the user's profile
  new_thread_id = str(uuid4())
  request.state.user.thread_ids.append(new_thread_id)
  db.user_profiles.update_one({"_id": ObjectId(request.state.user.id)}, {"$push": {"thread_ids": new_thread_id}})
  return StreamingResponse(stream_graph(state=state, thread_id=new_thread_id), media_type="text/event-stream")

@graph_app.post("/resume")
async def resume(request: Request, data: InterruptResume):
  # check user owns the thread_id
  user = request.state.user
  if data.thread_id not in user.thread_ids:
    raise HTTPException(403, "You do not have access to this thread_id")
  user_response = data.response
  config = {"configurable": {"thread_id": data.thread_id}}
  state = graph.get_state(config)
  if state is None:
    raise HTTPException(404, f"thread_id: {data.thread_id} not found!")
  if not state.next:
    raise HTTPException(500, "Operation cannot be resumed")
  if data.resume_from == "course_title_response" and state.next[0] == "course_title_response":
    user_answer = HumanMessage(content=user_response)
    graph.update_state(config, {"messages": [user_answer]})
  elif data.resume_from == "get_answer" and state.next[0] == "get_answer":
    graph.update_state(config, {"answers": user_response})
  elif data.resume_from == "get_course_target" and state.next[0] == "get_course_target":
    graph.update_state(config, {"course_target": user_response})
  elif data.resume_from == "content_creator_start" and state.next[0] == "content_creator_pause":
    # don't need to update state just resume
    graph.update_state(config, {"waiting_on": None})
  elif data.resume_from == "content_creator_resume" and state.next[0] == "content_creator_runner":
    graph.update_state(config, {"quiz_answers": user_response, "waiting_on": None})
  else:
    raise HTTPException(403, "Invalid response type")
  return StreamingResponse(stream_graph(state=None, thread_id=data.thread_id), media_type="text/event-stream")

@graph_app.post("/rerunlastnode")
async def rerun_last_node(request: Request, data: InterruptResume):
  # check user owns the thread_id
  user = request.state.user
  if user.thread_ids is None or data.thread_id not in user.thread_ids:
    raise HTTPException(403, "You do not have access to this thread_id")
  config = {"configurable": {"thread_id": data.thread_id}}
  checkpointers = list(checkpointer.list(config=config))
  if len(checkpointers) < 2:
    raise HTTPException(400, "No previous state to revert to")
  # get the second last checkpointer
  checkpoint = checkpointers[1]
  print("Reverting to checkpoint: ", checkpoint.config)
  checkpoint_id = checkpoint.config["configurable"]["checkpoint_id"]
  return StreamingResponse(stream_graph(state=None, thread_id=data.thread_id, checkpoint_id=checkpoint_id), media_type="text/event-stream")
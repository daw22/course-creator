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
from langgraph.types import Command

graph_app = APIRouter(prefix="/graph", tags=["graph"], dependencies=[Depends(get_current_user)])

class Answers(BaseModel):
  answers: List[str] | str
  thread_id: str | None

class InterruptResume(BaseModel):
  response: Any
  thread_id: str
  resume_from: str

async def stream_graph2(input: Command, thread_id: Optional[str], checkpoint_id: Optional[str] = None):
  if not thread_id:
    thread_id= str(uuid4())
  config = {"configurable": {"thread_id": thread_id, "checkpoint_id": checkpoint_id}}

  async for chunk in graph.astream(input, config, stream_mode="updates", subgraphs=True, version="v2"):
    node = list(chunk[1].keys())[0]
    current_state = graph.get_state(config, subgraphs=True)
    if node == "course_title_extractor":
      qort = current_state.values.get("qort", None)
      if qort and qort.get("course_title", None):
        # course title is decided
        yield f"{json.dumps({'type': 'on_course_title_decided', 'thread_id': thread_id, 'course_title': qort['course_title']})}"
    elif node == "course_title_response":
      qort = current_state.values.get("qort", None)
      if qort and qort.get("course_title", None):
        # course title is decided
        yield f"{json.dumps({'type': 'on_course_title_decided', 'thread_id': thread_id, 'course_title': qort['course_title']})}"
    elif node == "planner_app_runner":
      course_outline = current_state.values.get("course_outline", None)
      if course_outline:
        yield f"{json.dumps({'type': 'on_course_outline_generated', 'thread_id': thread_id, 'course_outline': course_outline})}"
    elif node == "create_course_record":
      course_id = current_state.values.get("course_id", None)
      if course_id:
        yield f"{json.dumps({'type': 'on_course_record_created', 'thread_id': thread_id, 'course_id': course_id})}"
    elif node == "store_content":
      course_progress = current_state.values.get("course_progress", [0, 0])
      yield f"{json.dumps({'type': 'on_subtopic_stored', 'thread_id': thread_id, 'course_progress': course_progress})}"
    elif node == "create_quiz":
      quiz = current_state.values.get("quiz", None)
      yield f"{json.dumps({'type': 'on_quiz_created', 'thread_id': thread_id})}"
    elif node == "store_quiz_result":
      quiz_results = current_state.tasks[0].state.values.get("quiz_results", None)
      yield f"{json.dumps({'type': 'on_quiz_result_stored', 'thread_id': thread_id, 'quiz_results': quiz_results})}"
    elif node == "__interrupt__":
      print("Interrupt node reached:", current_state)
      print("Next nodes:", current_state.next[0] if current_state.next else "None")
      if current_state.next[0] == "course_title_response":
        qort = current_state.values.get("qort", None)
        if qort and qort.get("question", None):
          # course title is decided
          yield f"{json.dumps({'type': 'on_title_clarification', 'thread_id': thread_id, 'question': current_state.values['qort']['question']})}"
      elif current_state.next[0] == "get_answer":
        questions = current_state.values.get("questions", [])
        yield f"{json.dumps({'type': 'on_prerequisite_questions', 'thread_id': thread_id, 'questions': questions})}"
      elif current_state.next[0] == "get_course_target":
        course_target_suggestion = current_state.values.get("course_target_suggestion", None)
        yield f"{json.dumps({'type': 'on_course_target_suggestion', 'thread_id': thread_id, 'course_target_suggestion': course_target_suggestion})}"
      elif current_state.next[0] == "content_creator_pause":
        course_outline = current_state.values.get("course_outline", None)
        course_progress = current_state.values.get("course_progress", [0, 0])
        subtopic_to_generate = course_outline[course_progress[0]]["subtopics"][course_progress[1]]
        yield f"{json.dumps({'type': 'on_content_creation_start', 'thread_id': thread_id, 'subtopic_title': subtopic_to_generate['subtopic_title'], 'subtopic_target': subtopic_to_generate['subtopic_target']})}"
      elif current_state.next[0] == "content_creator_runner":
        quiz = current_state.tasks[0].state.values.get("quiz", None)
        yield f"{json.dumps({'type': 'on_quiz_time', 'thread_id': thread_id, 'quiz': quiz})}"   


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
  return StreamingResponse(stream_graph2(input=state, thread_id=new_thread_id), media_type="text/event-stream")

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
    input = Command(resume=user_answer)
  elif data.resume_from == "get_answer" and state.next[0] == "get_answer":
    input = Command(resume=user_response)
  elif data.resume_from == "get_course_target" and state.next[0] == "get_course_target":
    input = Command(resume=user_response)
  elif data.resume_from == "content_creator_start" and state.next[0] == "content_creator_pause":
    # don't need to update state just resume
    input = None
  elif data.resume_from == "content_creator_resume" and state.next[0] == "content_creator_runner":
    input = Command(resume=user_response)
  else:
    raise HTTPException(403, "Invalid response type")
  return StreamingResponse(stream_graph2(input=input, thread_id=data.thread_id), media_type="text/event-stream")

# @graph_app.post("/rerunlastnode")
# async def rerun_last_node(request: Request, data: InterruptResume):
#   # check user owns the thread_id
#   user = request.state.user
#   if user.thread_ids is None or data.thread_id not in user.thread_ids:
#     raise HTTPException(403, "You do not have access to this thread_id")
#   config = {"configurable": {"thread_id": data.thread_id}}
#   checkpointers = list(checkpointer.list(config=config))
#   if len(checkpointers) < 2:
#     raise HTTPException(400, "No previous state to revert to")
#   # get the second last checkpointer
#   checkpoint = checkpointers[-1]
#   print("Reverting to checkpoint: ", checkpoint.config)
#   checkpoint_id = checkpoint.config["configurable"]["checkpoint_id"]
#   return StreamingResponse(stream_graph(input=None, thread_id=data.thread_id, checkpoint_id=checkpoint_id), media_type="text/event-stream")
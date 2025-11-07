from bson import ObjectId
from prerequisite_analyzer.agent import app as graph
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel
from typing import Any
from fastapi.responses import StreamingResponse
from uuid import uuid4
from app.dependencies import get_current_user
from app.db.connection import db
from fastapi import Depends, Request
from app.db.connection import checkpointer
from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from app.utils import stream_graph

graph_app = APIRouter(prefix="/graph", tags=["graph"], dependencies=[Depends(get_current_user)])

class StartInput(BaseModel):
  answer: str

class ThreadIdResponse(BaseModel):
  thread_id: str

class InterruptResume(BaseModel):
  response: Any | None
  thread_id: str
  resume_from: str


@graph_app.post("/start")
async def start(request: Request, data: StartInput):
  state = {"messages": [HumanMessage(content=f"Hi there! I am {request.state.user.first_name}"),
                        AIMessage(content=f"Hello {request.state.user.first_name}! What do you want to learn about today?"),
                        HumanMessage(content=f"{data.answer}")], 
           "user_id": str(request.state.user.id)}
  # create and add the new thread_id to the user's profile
  new_thread_id = str(uuid4())
  request.state.user.thread_ids.append(new_thread_id)
  db.user_profiles.update_one({"_id": ObjectId(request.state.user.id)}, {"$push": {"thread_ids": new_thread_id}})
  return StreamingResponse(stream_graph(input=state, thread_id=new_thread_id), 
                          media_type="text/event-stream",
                          headers={
                               "Cache-Control": "no-cache",
                               "Connection": "keep-alive",
                               "X-Accel-Buffering": "no",  # Prevent proxy buffering
                               "Access-Control-Allow-Origin": "https://ai-course-creator-frontend.vercel.app/",
                               "Access-Control-Allow-Credentials": "true",
                           },
                           )

@graph_app.post("/resume")
async def resume(request: Request, data: InterruptResume):
  # check user owns the thread_id
  user = request.state.user
  if data.thread_id not in user.thread_ids:
    raise HTTPException(403, "You do not have access to this thread_id")
  user_response = data.response
  config = {"configurable": {"thread_id": data.thread_id}}
  state = graph.get_state(config, subgraphs=True)
  print("Resuming from state next:", state.next[0] if state.next else "No next", "for thread_id:", data.thread_id)
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
  elif data.resume_from == "content_creator_start":
    # don't need to update state just resume
    input = Command(resume=user_response)
  # elif data.resume_from == "content_creator_resume" and state.next[0] == "content_creator_runner":
  #   input = Command(resume=user_response)
  elif data.resume_from == "outline_approval":
    input = Command(resume=user_response)
  else:
    raise HTTPException(403, "Invalid response type")
  return StreamingResponse(stream_graph(input=input, thread_id=data.thread_id), 
                           media_type="text/event-stream",
                           headers={
                               "Cache-Control": "no-cache",
                               "Connection": "keep-alive",
                               "X-Accel-Buffering": "no",  # Prevent proxy buffering
                               "Access-Control-Allow-Origin": "https://ai-course-creator-frontend.vercel.app/",
                               "Access-Control-Allow-Credentials": "true",
                           },
                          )

@graph_app.post("/rerunlastnode")
async def rerun_last_node(request: Request, data: ThreadIdResponse):
  # check user owns the thread_id
  user = request.state.user
  if data.thread_id not in user.thread_ids:
    raise HTTPException(403, "You do not have access to this thread_id")
  config = {"configurable": {"thread_id": data.thread_id}}
  checkpointers = list(checkpointer.list(config=config))
  if len(checkpointers) < 2:
    raise HTTPException(400, "No previous state to revert to")
  # get the second last checkpointer
  checkpoint = checkpointers[1]
  # print("Reverting to checkpoint: ", checkpoint.config)
  checkpoint_id = checkpoint.config["configurable"]["checkpoint_id"]
  return StreamingResponse(stream_graph(input=None, thread_id=data.thread_id, checkpoint_id=checkpoint_id), media_type="text/event-stream")

@graph_app.post("/rerunfromcheckpoint")
async def rerun_from_checkpoint(request: Request, data: InterruptResume):
  # check user owns the thread_id
  user = request.state.user
  if data.thread_id not in user.thread_ids:
    raise HTTPException(403, "You do not have access to this thread_id")
  return StreamingResponse(stream_graph(input=Command(resume=data.response), thread_id=data.thread_id, checkpoint_id=data.resume_from), media_type="text/event-stream")

@graph_app.post("/delete_thread")
async def delete_thread(request: Request, data: ThreadIdResponse):
  # check user owns the thread_id
  user = request.state.user
  if data.thread_id not in user.thread_ids:
    raise HTTPException(403, "You do not have access to this thread_id")
  # remove the thread_id from the user's profile
  db.user_profiles.update_one({"_id": ObjectId(user.id)}, {"$pull": {"thread_ids": data.thread_id}})
  # delete the course associated with the thread_id
  db.courses.delete_many({"thread_id": data.thread_id})
  # delete all checkpointers associated with the thread_id
  checkpointer.adelete_thread(data.thread_id)
  return {"message": "Thread deleted successfully"}
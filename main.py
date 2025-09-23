""""
 - ask the user to enter a course title (HMIL) eg- "Hey there, what are you looking to learn about?"
 - get course title (make sure we have a valid course title)-> make the llm decide and use a router
 - identify all the prerequisites(a node)
 - create questions for the prerequisites(a node)
 (in a way they can be answered like 'need a refresher', 'no experiance', 'no refresher needed')
 - save the questions
 - collect answers for all the questions and save them
 - create a summary(or structured output) describing what to include in the course and to what extent
 agent-state
 - questions
 - answers
 - course_title(extracted cource title from user query/s)
 - custom-request
 - output
 - messages(back and forth between the agent and the user, if the user doesen't provide a clear course title there
 will be more than two messages here) this will be used to try extract the course title
 final output format
 {
   "user_knowledge_summary": str,
   "course_tite": str,
   "prerequisites" : [
      {
         "prerequsite_name": str,
         "user_answer": str
         "assesment": str
      }
   ],
   "special_request": str
 }

 """

"""
application flow
-> user provides a course output
-> an agent asks the user several questions to know the user knowledge level on the prerequesites
-> depending on the answer the agent desides which prerequisites to include in the course and to what extent(light refresher, full introduction)
-> using the above output another agent creates the actual course
** the actual course creation???
-> the agent identifies the major topics of the course(chapter level topics) and subtopics for each topic, and they will be saved(db)
-> the first chapter could be for prerequisites
-> the agent creates the actual test/contet on a sub-topic level, when generating this content the agent should have context about
   - summary of the previous topic - summary about the whole course - the target of this subtopic - prefered layout ot the sub-topic
-> 
"""

from prerequisite_analyzer.agent import app
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from uuid import uuid4
from pydantic import BaseModel
from typing import List, Optional
import json

class Answers(BaseModel):
  answers: List[str]
  thread_id: str

class InterruptResume(BaseModel):
  response: str | list[str]
  thread_id: str

server = FastAPI()


async def stream_graph(state: Optional[dict], thread_id: Optional[str]):
  if not thread_id:
    thread_id = str(uuid4())
  config = {"configurable": {"thread_id": thread_id}}
  async for chunk in app.astream_events(state, config, version="v2"):
    data = chunk["data"]
    kind = chunk["event"]
    name = chunk["name"]
    print(chunk, "\n\n")
    current_state = app.get_state(config)
    print("state: ", current_state, "\n\n")
    if kind == "on_chain_start":
      if name == "LangGraph":
        yield f"{json.dumps({"type": "on_app_start", "thread_id": thread_id})}"
    if kind == "on_chain_end":
      if name == "LangGraph":
        current_state = app.get_state(config)
        if current_state.next:  
          if current_state.next[0] == "course_title_response":
            yield f"{json.dumps({"type": "on_title_clarification", "thread_id": thread_id, "question": current_state.values["qort"]["question"]})}"
          if current_state.next[0] == "get_answer":
            yield f"{json.dumps({"type": "on_prerequisite_questions", "thread_id": thread_id, "questions": current_state.values["questions"]})}"  
        else:
          yield f"{json.dumps({"type": "on_prerequistes_report", "thread_id": thread_id, "output": current_state.values["output"]})}"

@server.get("/start")
async def start():
  state = {"messages": [HumanMessage(content="hi")]}
  return StreamingResponse(stream_graph(state=state, thread_id=None), media_type="text/event-stream")

@server.post("/resume")
async def resume(data: InterruptResume):
  user_response = data.response
  config = {"configurable": {"thread_id": data.thread_id}}
  state = app.get_state(config)
  if state is None:
    raise HTTPException(404, f"thread_id: {data.thread_id} not found!")
  if not state.next:
    raise HTTPException(500, "Operation cannot be resumed")
  if isinstance(user_response, str) and state.next[0] == "course_title_response":
    user_answer = HumanMessage(content=user_response)
    app.update_state(config, {"messages": [user_answer]})
  elif isinstance(user_response, list):
    app.update_state(config, {"answers": user_response})
  else:
    raise HTTPException(403, "Invalid response type")
  return StreamingResponse(stream_graph(state=None, thread_id=data.thread_id), media_type="text/event-stream")

import uvicorn
if __name__ == "__main__":
  uvicorn.run(server, host="0.0.0.0", port=8080)
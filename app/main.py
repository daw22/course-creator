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


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes.auth import router as auth_router
from app.routes.graph import graph_app
from app.routes.courses import courses_router
import os
from pymongo import MongoClient
load_dotenv()


app = FastAPI()
# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#db instance
client = MongoClient(os.getenv("DB_URI"))
db = client["course_creator"]

app.include_router(auth_router)
app.include_router(graph_app)
app.include_router(courses_router)


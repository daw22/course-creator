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
from langchain_core.messages import HumanMessage

# state = {"course_title": "introuduction to Mechanical vibrations"}
state = {"messages": [HumanMessage(content="hi")]}
config = {"configurable": {"thread_id": "1"}}

#start app
app.invoke(state, config)

state = app.get_state(config)
print(state)
# if question asked
course_title = state.values["qort"]["course_title"]
while course_title == None:
  # get question
  question = state.values["qort"]["question"]
  answer = input(f"question: {question} \nanswer: ")
  app.invoke(Command(resume=answer), config)
  state = app.get_state(config)
  print(state)
  course_title = state.values["qort"]["course_title"]
  print("coures_title: ", course_title)

after_title_state = app.get_state(config)
print("after title state: ", after_title_state)
# after getting course title and generating the questions

answers = []
for question in state.values["questions"]:
  answer_pq = input(f"{question} \n answers: ")
  answers.append(answer_pq)

app.invoke(Command(resume=answers), config)
end_state = app.get_state(config)
print("end state: ", end_state)

# no_questions = len(state.values["questions"])
# answers = ["need a refresher"] * no_questions

# print("state1: ", state)

# app.update_state(config, {"answers": answers})


# app.invoke(Command(resume=answers), config)

# state = app.get_state(config)
# print("state2: ",state)
# print(f"{len(state.values["answers"])} == {len(state.values["questions"])}")
 
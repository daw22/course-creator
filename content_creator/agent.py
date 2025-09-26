"""
*** THE CONTENT CREATOR***
purpose -> it generates text based on a topic and some aditional info
inputs -> course_title, users_proficency on the prerequisites
steps
=====
1 - creates topics and subtopics for the course by including the recomended prerequisites
 -> target of the course
 -> steps to reach the target(sub-topics and chapters as steps one leading to the other)
 -> create chapter, the first being addressing the prerequisites
 -> create sub targets per chapter considering the target of the course
 -> sub-topics in a chapter further create sub target used to achive target of the chapter
2- create content for each topic
   -> For chapters
     -- introduction, stating the target of the chapter, what the user learns, introductory topics
     -- subtopics, trying to achive the learnning target
     -- quiz at the end of every chapter
3- save already generated content(vector DBs)
4- enable document chating with the already generated content
5- track user progress
6- create a mechanism to choose between generating a new content and loading one already generated
3- sub-topic
-> websearch and reference handling

learning tatget -> subtarget -> chapters -> subtarget -> subtopics -> content

what to save
-> the content with the subtarget and summary of it(list of key points)
-> the quiz with the answers
"""
from prerequisite_analyzer.state import AgentState


def subtarget_creator(state: AgentState):
    pass
import json
from typing import Optional
from uuid import uuid4
from prerequisite_analyzer.agent import app as graph
from langgraph.types import Command

async def stream_graph(input: Command, thread_id: Optional[str], checkpoint_id: Optional[str]= None):
  if not thread_id:
    thread_id = str(uuid4())
  config = {"configurable": {"thread_id": thread_id, "checkpoint_id": checkpoint_id}}

  async for chunk in graph.astream_events(input, config, version="v2"):
    event = chunk["event"]
    name = chunk["name"]
    data = chunk["data"]
    snapshots = list(graph.get_state_history(config))
    if snapshots and len(snapshots) > 0:
      last_snapshot = snapshots[0]
      config  = last_snapshot.config
    if event == "on_chain_start":
      # this are the interrupt nodes
      if name == "__start__":
        yield f"event: on_chain_start\ndata: {json.dumps({'config': config})}\n\n"
      if name == "course_title_response":
        if last_snapshot and not last_snapshot.interrupts:
          yield f"event: on_course_title_question\ndata: {json.dumps({'config': config, 'question': data['input']['qort']['question']})}\n\n"
      if name == "get_answer":
        if last_snapshot and not last_snapshot.interrupts:
          yield f"event: on_prerequisite_questions\ndata: {json.dumps({'config': config, 'questions': data['input']['questions']})}\n\n"
      if name == "content_creator_pause":
        course_outline = data["input"]["course_outline"]
        course_progress = data["input"].get("course_progress", [0, 0])
        outline = data["input"]["course_outline"]
        if course_progress[0] >= len(outline) and course_progress[1] >= len(outline[-1]["subtopics"]):
          # course complete
          yield f"event: on_course_complete\ndata: {json.dumps({'config': config})}\n\n"
        else:
          last_snapshot = list(graph.get_state_history(config))[0]
          if last_snapshot and not last_snapshot.interrupts:
            subtopic_to_generate = course_outline[course_progress[0]]["subtopics"][course_progress[1]]
            yield f"event: on_content_creation_start\ndata: {json.dumps({'config': config, 
                                 'subtopic_title': subtopic_to_generate['subtopic_title'],
                                 'subtopic_target': subtopic_to_generate['subtopic_target'], 'course_progress': course_progress})}\n\n"
    elif event == "on_chat_model_stream":
      print("CHAT MODEL STREAM CHUNK -", name, ":", chunk)
      if name == "generate_content":
        yield f"event: on_content_stream\ndata: {json.dumps({'config': config, 'content': chunk['message']['content']})}\n\n"
    elif event == "on_chain_stream":
      if data.get("chunk") and "__interrupt__" in data["chunk"]:
        print(f"Interrupt chunk - {name}:", data["chunk"]["__interrupt__"])
        # yield f"{json.dumps({'type': 'on_interrupt', 'config': config, 'interrupt': data['chunk']['__interrupt__'].value})}"
    elif event == "on_chain_end":
      # need to send the previous checkpoint for a possible replay
      previous_snapshot = list(graph.get_state_history(config))[1]
      if previous_snapshot:
        config = previous_snapshot.config
      if name == "course_title_extractor":
        if data["output"]["qort"]["course_title"]:
          yield f"event: on_course_title_decided\ndata: {json.dumps({'config': config, 'course_title': data['output']['course_title']})}\n\n"
      if name == "planner_app_runner":
        yield f"event: on_course_outline_generated\ndata: {json.dumps({'config': config, 'course_outline': data['output']['course_outline']})}\n\n"
      if name == "create_course_record":
        yield f"event: on_course_record_created\ndata: {json.dumps({'config': config, 'course_id': data['output']['course_id']})}\n\n"
      if name == "suggest_course_target":
        yield f"event: on_course_target_suggestion\ndata: {json.dumps({'config': config, 'course_target_suggestion': data['output']['course_target_suggestion']})}\n\n"
      if name == "get_course_target":
        print("state:", graph.get_state(config).values)
        # course_target_suggestion = graph.get_state(config).values["course_target_suggestion"]
        target_index = data['output']['course_target']
        yield f"event: on_course_target_picked\ndata: {json.dumps({'config': config, 'course_target_picked': target_index})}\n\n"
      if name == "create_quiz":
        yield f"event: on_quiz_created\ndata: {json.dumps({'config': config, 'quiz': data['output']['quiz']})}\n\n"
      if name == "store_quiz_result":
        print("Store quiz result node ended:", data['output'])
        yield f"event: on_quiz_result_stored\ndata: {json.dumps({'config': config, 'quiz_results': data['output']['quiz_results']})}\n\n"


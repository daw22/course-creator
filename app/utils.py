import json
from typing import Optional
from uuid import uuid4
from prerequisite_analyzer.agent import app as graph
from langgraph.types import Command

async def stream_graph(input: Command, thread_id: Optional[str], checkpoint_id: Optional[str]= None):
  if not thread_id:
    thread_id = str(uuid4())
  config = {"configurable": {"thread_id": thread_id, "checkpoint_id": checkpoint_id}}
  try:
    async for chunk in graph.astream_events(input, config, version="v2"):
      event = chunk["event"]
      name = chunk["name"]
      data = chunk["data"]
      metadata = chunk["metadata"]
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
          outline = data["input"]["course_outline"]["chapters"]
          if course_progress[0] >= len(outline) and course_progress[1] >= len(outline[-1]["subtopics"]):
            # course complete
            yield f"event: on_course_complete\ndata: {json.dumps({'config': config})}\n\n"
          else:
            last_snapshot = list(graph.get_state_history(config))[0]
            if last_snapshot and not last_snapshot.interrupts:
              subtopic_to_generate = course_outline["chapters"][course_progress[0]]["subtopics"][course_progress[1]]
              yield f"event: on_content_creation_start\ndata: {json.dumps({'config': config, 
                                   'subtopic_title': subtopic_to_generate['subtopic_title'],
                                   'subtopic_target': subtopic_to_generate['subtopic_target'], 'course_progress': course_progress})}\n\n"
      elif event == "on_chat_model_stream":
        print("CHAT MODEL STREAM CHUNK -", name, ":", chunk)
        if metadata.get("langgraph_node", "") == "generate_content":
          yield f"event: on_markdown_stream\ndata: {json.dumps({'config': config, 'markdown': chunk['data']['chunk'].content})}\n\n"
      elif event == "on_chain_stream":
        if data.get("chunk") and "__interrupt__" in data["chunk"]:
          # print(f"Interrupt chunk - {name}:", data["chunk"]["__interrupt__"][0].value)
          yield f"event: on_chain_interrupt\ndata: {json.dumps({'config': config, 'interrupt': data['chunk']['__interrupt__'][0].value})}\n\n"
      elif event == "on_chain_end":
        # need to send the previous checkpoint for a possible replay
        previous_snapshot = list(graph.get_state_history(config))[1]
        if previous_snapshot:
          config = previous_snapshot.config
        if name == "course_title_extractor":
          if data["output"]["qort"]["course_title"]:
            yield f"event: on_course_title_decided\ndata: {json.dumps({'config': config, 'course_title': data['output']['course_title']})}\n\n"
        if name == "course_outline_creator":
          yield f"event: on_course_outline_generated\ndata: {json.dumps({'config': config, 'course_outline': data['output']['course_outline']})}\n\n"
        if name == "create_course_record":
          yield f"event: on_course_record_created\ndata: {json.dumps({'config': config, 'course_id': data['output']['course_id']})}\n\n"
        if name == "suggest_course_target":
          yield f"event: on_course_target_suggestion\ndata: {json.dumps({'config': config, 'course_target_suggestion': data['output']['course_target_suggestion']})}\n\n"
        if name == "get_course_target":
          target_index = data['output']['course_target']
          yield f"event: on_course_target_picked\ndata: {json.dumps({'config': config, 'course_target_picked': target_index})}\n\n"
        if metadata.get("langgraph_node", "") == "generate_content":
          yield f"event: on_content_generation_complete\ndata: {json.dumps({'config': config})}\n\n"
  except Exception as e:
    print("Error during graph streaming:", str(e))
    name = chunk["name"]
    data = chunk["data"]
    snapshots = list(graph.get_state_history(config))
    if snapshots and len(snapshots) > 0:
      last_snapshot = snapshots[0]
      config  = last_snapshot.config
    yield f"event: on_error\ndata: {json.dumps({'node': name, 'config': config })}\n\n"
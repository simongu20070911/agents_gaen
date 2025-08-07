import uuid

def ensure_tool_call_ids(callback_context, llm_request):
    if llm_request.tool_calls:
        for tool_call in llm_request.tool_calls:
            if tool_call.id is None:
                tool_call.id = str(uuid.uuid4())
    return llm_request
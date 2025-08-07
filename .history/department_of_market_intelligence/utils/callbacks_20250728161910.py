import uuid

def ensure_tool_call_ids(callback_context, llm_request):
    if llm_request.tool_calls:
        for tool_call in llm_request.tool_calls:
            if tool_call.id is None:
                tool_call.id = str(uuid.uuid4())
    return llm_request

def ensure_end_of_output(callback_context, llm_response):
    if llm_response.text and not llm_response.text.endswith("<end of output>"):
        llm_response.text += "\n<end of output>"
    return llm_response
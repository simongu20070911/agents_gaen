import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock

from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, LlmChunk
from google.genai.types import Content, Part

from department_of_market_intelligence.workflows.coder_workflow import CoderWorkflowAgent
from department_of_market_intelligence import config

@pytest.mark.asyncio
async def test_thinking_tokens_are_streamed():
    # Arrange
    # Set up a mock manifest and task
    manifest_path = "/tmp/test_manifest.json"
    task = {
        "task_id": "test_task",
        "description": "A test task",
        "dependencies": [],
        "input_artifacts": [],
        "output_artifacts": ["/tmp/output.py"],
        "success_criteria": ["The file is created."]
    }

    with open(manifest_path, "w") as f:
        import json
        json.dump([task], f)

    # Mock the context and session state
    mock_session = MagicMock()
    mock_session.state = {
        "implementation_manifest_artifact": manifest_path,
        "coder_subtask": task,
        "artifact_to_validate": f"coder_output_{task['task_id']}",
        "validation_version": 0,
    }
    
    # Mock the ADK's context
    ctx = InvocationContext(
        session=mock_session,
        # Mock other necessary context properties if needed
    )

    # Set a specific model for the test to ensure we're not using a mock
    original_coder_model = config.CODER_MODEL
    config.CODER_MODEL = "gemini/gemini-1.5-flash-latest" # A fast model for testing
    config.DRY_RUN_MODE = False # Ensure we're not in dry run mode

    # The agent to test
    agent = CoderWorkflowAgent(name="TestCoderWorkflow")

    thinking_found = False

    # Act
    async for event in agent.run_async(ctx):
        if isinstance(event, LlmChunk):
            if "thinking" in event.content.parts[0].text.lower():
                thinking_found = True
                print(f"Found thinking chunk: {event.content.parts[0].text}")
                break # We found what we were looking for

    # Assert
    assert thinking_found, "No 'thinking' tokens were found in the streamed LLM chunks."

    # Teardown
    import os
    os.remove(manifest_path)
    config.CODER_MODEL = original_coder_model

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from department_of_market_intelligence.utils.streaming_lite_llm import StreamingLiteLLM

# Mock the litellm library
@pytest.fixture
def mock_litellm():
    mock = MagicMock()
    
    async def mock_completion(*args, **kwargs):
        # Simulate a streaming response
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" "))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="World"))]),
        ]
        for chunk in chunks:
            yield chunk
            await asyncio.sleep(0.01)

    mock.completion = AsyncMock(side_effect=mock_completion)
    return mock

@pytest.mark.asyncio
async def test_streaming_lite_llm_wrapper(mock_litellm):
    """Test that the StreamingLiteLLM wrapper correctly streams responses."""
    
    # Replace the litellm module with our mock
    import sys
    sys.modules['litellm'] = mock_litellm
    
    # Instantiate the wrapper
    streaming_llm = StreamingLiteLLM()
    
    # Define test parameters
    model = "test-model"
    messages = [{"role": "user", "content": "test"}]
    
    # Call the completion method
    response_stream = streaming_llm.completion(model=model, messages=messages, stream=True)
    
    # Collect the streamed chunks
    chunks = [chunk async for chunk in response_stream]
    
    # Assert that the chunks are correct
    assert len(chunks) == 3
    assert chunks[0].choices[0].delta.content == "Hello"
    assert chunks[1].choices[0].delta.content == " "
    assert chunks[2].choices[0].delta.content == "World"
    
    # Verify that litellm.completion was called correctly
    mock_litellm.completion.assert_called_once_with(
        model=model,
        messages=messages,
        stream=True
    )
    
    # Clean up the mock
    del sys.modules['litellm']
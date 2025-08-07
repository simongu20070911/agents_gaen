import asyncio
import litellm
from department_of_market_intelligence import config

async def main():
    """Test streaming completion from the configured endpoint."""
    
    # Set the custom endpoint and API key
    api_base = config.CUSTOM_GEMINI_API_ENDPOINT
    if not api_base.endswith("/v1"):
        api_base = f"{api_base.rstrip('/')}/v1"
    litellm.api_base = api_base
    litellm.api_key = config.CUSTOM_API_KEY
    
    model = f"custom/{config.CHIEF_RESEARCHER_MODEL}"
    messages = [{"role": "user", "content": "Hello, world!"}]
    
    print(f"--- Testing streaming completion for model: {model} ---")
    print(f"--- Endpoint: {litellm.api_base} ---")
    
    try:
        # Call the completion method with streaming enabled
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            stream=True
        )
        
        # Print the streamed chunks
        async for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        
        print("\n--- Streaming test completed successfully! ---")
        
    except Exception as e:
        print(f"\n--- An error occurred during the streaming test: {e} ---")

if __name__ == "__main__":
    asyncio.run(main())
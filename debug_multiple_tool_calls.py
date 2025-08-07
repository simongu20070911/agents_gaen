#!/usr/bin/env python3
"""Debug script to understand why only first tool call is executed."""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Enable verbose logging
os.environ['EXECUTION_MODE'] = 'dry_run'

from department_of_market_intelligence import config
config.VERBOSE_LOGGING = True
config.EXECUTION_MODE = "dry_run"
config.DRY_RUN_SKIP_LLM = False

import asyncio
from google.adk.runners import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.genai import types
from department_of_market_intelligence.utils.model_loader import get_llm_model
from department_of_market_intelligence.tools.toolset_registry import toolset_registry
from department_of_market_intelligence.tools.mock_tools import mock_desktop_commander_toolset

async def debug_multiple_calls():
    """Debug multiple tool calls."""
    
    print("🔍 DEBUGGING MULTIPLE TOOL CALLS")
    print("="*60)
    
    # Set up mock tools
    toolset_registry.set_desktop_commander_toolset(mock_desktop_commander_toolset, is_real_mcp=False)
    
    # Create test agent with explicit multiple tool call instruction
    test_agent = LlmAgent(
        model=get_llm_model("gemini-2.5-flash"),
        name="DebugMultiToolAgent",
        instruction="""You are a debug agent. Your ONLY job is to make exactly 2 tool calls in your response.

CRITICAL: You MUST make BOTH of these tool calls in a SINGLE response:
1. First, call create_directory with path="/tmp/test_dir"
2. Second, call write_file with path="/tmp/test_dir/test.txt" and content="Test content"

Make both tool calls now. Do not explain, just make the tool calls.""",
        tools=mock_desktop_commander_toolset
    )
    
    # Create session
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="debug_app", user_id="debug_user")
    
    # Create runner with logging
    runner = Runner(
        agent=test_agent,
        app_name="debug_app",
        session_service=session_service
    )
    
    print("\n📤 Sending request...")
    
    # Track events
    events = []
    tool_calls_found = []
    
    # Send simple message
    user_message = types.Content(
        role="user",
        parts=[types.Part(text="Make the two tool calls now")]
    )
    
    # Run and collect events
    async for event in runner.run_async(
        user_id="debug_user",
        session_id=session.id,
        new_message=user_message
    ):
        events.append(event)
        
        # Check for function calls in the event
        if hasattr(event, 'get_function_calls'):
            func_calls = event.get_function_calls()
            if func_calls:
                print(f"\n🔧 Found {len(func_calls)} function calls in event {event.id}:")
                for i, fc in enumerate(func_calls):
                    print(f"   {i+1}. {fc.name} - {fc.args}")
                    tool_calls_found.append(fc)
        
        # Check event content
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    print(f"   📌 Part has function_call: {part.function_call.name}")
                if hasattr(part, 'text') and part.text:
                    print(f"   📝 Text: {part.text[:100]}...")
    
    print(f"\n📊 Summary:")
    print(f"Total events: {len(events)}")
    print(f"Total tool calls found: {len(tool_calls_found)}")
    
    if len(tool_calls_found) < 2:
        print("\n❌ ISSUE CONFIRMED: Less than 2 tool calls were found!")
        print("This confirms the model is generating multiple calls but they're not being parsed/executed.")
    else:
        print("\n✅ Multiple tool calls were found and executed!")

if __name__ == "__main__":
    asyncio.run(debug_multiple_calls())
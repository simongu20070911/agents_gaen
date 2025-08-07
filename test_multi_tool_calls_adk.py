#!/usr/bin/env python3
"""Test multiple tool calls with ADK"""

import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
import asyncio
from google.adk.events import Event

def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city."""
    print(f"🌤️  TOOL CALLED: get_weather(city='{city}')")
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    print(f"🕐 TOOL CALLED: get_current_time(city='{city}')")
    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}


async def main():
    print("🧪 TESTING MULTIPLE TOOL CALLS IN ADK")
    print("=" * 50)
    
    # Create agent with multiple tools
    root_agent = Agent(
        name="weather_time_agent",
        model="gemini-2.0-flash",
        description=(
            "Agent to answer questions about the time and weather in a city."
        ),
        instruction=(
            "You are a helpful agent who can answer user questions about the time and weather in a city. "
            "When asked about both weather and time, make sure to call BOTH tools in a single response."
        ),
        tools=[get_weather, get_current_time],
    )
    
    # Test query that should trigger multiple tools
    query = "What's the weather and current time in New York? Please use both tools in ONE response."
    print(f"📝 Query: {query}")
    print("=" * 50)
    
    # Create session and context
    from google.adk.agents.invocation_context import InvocationContext
    from google.adk.sessions import Session
    
    session = Session(
        id="test-session",
        appName="test-app",
        userId="test-user"
    )
    ctx = InvocationContext(
        input_text=query,
        session=session,
        agent=root_agent
    )
    
    # Run the agent
    tool_calls_count = 0
    events_count = 0
    
    async for event in root_agent.run_async(ctx):
        events_count += 1
        if event.author and event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call:
                    tool_calls_count += 1
                    print(f"✅ Tool call #{tool_calls_count}: {part.function_call.name}")
                if part.text:
                    print(f"[{event.author}]: {part.text.strip()}")
    
    print("=" * 50)
    print(f"📊 Summary:")
    print(f"   Total events: {events_count}")
    print(f"   Total tool calls: {tool_calls_count}")
    
    if tool_calls_count >= 2:
        print("✅ SUCCESS: Multiple tool calls were made!")
    else:
        print("❌ ISSUE: Only one tool call was made")


if __name__ == "__main__":
    asyncio.run(main())
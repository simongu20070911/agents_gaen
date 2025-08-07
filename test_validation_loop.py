#!/usr/bin/env python3
"""Test the validation loop fix."""

import asyncio
import sys
import os
sys.path.insert(0, '/home/gaen/agents_gaen')

from department_of_market_intelligence import config
from department_of_market_intelligence.workflows.research_planning_workflow_context_aware import (
    get_context_aware_research_planning_workflow
)
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions import InMemorySession

# Set dry run mode for testing
config.DRY_RUN_MODE = False
config.DRY_RUN_SKIP_LLM = False
config.MAX_PLAN_REFINEMENT_LOOPS = 2  # Limit iterations for testing
config.PARALLEL_VALIDATION_SAMPLES = 2  # Reduce parallel validators

async def test_validation_loop():
    """Test the validation loop with Chief Researcher creating new versions."""
    
    print("🧪 Testing validation loop fix...")
    
    # Create session with initial state
    session = InMemorySession()
    session.state['task_id'] = 'sample_research_task'
    session.state['current_task'] = 'generate_initial_plan'
    session.state['plan_version'] = 0
    session.state['validation_version'] = 0
    
    # Create workflow
    workflow = get_context_aware_research_planning_workflow()
    
    # Create invocation context
    ctx = InvocationContext(session=session)
    
    # Run workflow
    try:
        print("🚀 Starting workflow...")
        async for event in workflow.run_async(ctx):
            # Process events (could log them if needed)
            pass
        
        print("✅ Workflow completed successfully")
        
        # Check final state
        print(f"\n📊 Final state:")
        print(f"   Plan version: {session.state.get('plan_version', 'unknown')}")
        print(f"   Validation status: {session.state.get('validation_status', 'unknown')}")
        print(f"   Current task: {session.state.get('current_task', 'unknown')}")
        
        # Check created files
        outputs_dir = config.get_outputs_dir('sample_research_task')
        import glob
        plans = glob.glob(f"{outputs_dir}/planning/research_plan_v*.md")
        critiques = glob.glob(f"{outputs_dir}/planning/critiques/*.md")
        
        print(f"\n📁 Files created:")
        print(f"   Research plans: {len(plans)}")
        for plan in sorted(plans):
            print(f"      - {os.path.basename(plan)}")
        print(f"   Critiques: {len(critiques)}")
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_validation_loop())
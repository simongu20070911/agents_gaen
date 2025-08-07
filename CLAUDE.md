# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a multi-project repository containing various AI agent implementations:

1. **solver/** - IMO (International Mathematical Olympiad) Solver Agent Pipeline
2. **adk-docs/** - Agent Development Kit (ADK) Documentation and Examples
3. **alphagpt/** - (Empty directory, possibly for future AlphaGPT implementation)
4. **equity_research_team/** - (Empty directory, possibly for future equity research agent team)

## IMO Solver Project (`/solver`)

### Overview
A sophisticated multi-agent LLM system for solving IMO-level mathematical problems using 5 specialized agents in a hierarchical pipeline.

### Common Development Commands

```bash
# Run the main solver pipeline
cd solver
python -m solver.main

# Run specific test scripts
python test_parallel_trajectories_clean.py  # Test parallel trajectory mode
python test_thinking_streaming.py          # Test streaming functionality

# Run tests with pytest (if installed)
python -m pytest
```

### Architecture

**5-Agent Pipeline** (defined in `pipeline.py`):
1. **Generator Agent** - Creates initial solution attempts
2. **Self-Improvement Agent** - Refines incomplete solutions
3. **Verifier Agent** - Identifies errors in solutions
4. **Meta-Verifier Agent** - Reviews and filters bug reports
5. **Correction Agent** - Produces corrected final solutions

**Key Files**:
- `main.py` - Main entry point with checkpoint/resume support
- `main_parallel_trajectories.py` - Parallel trajectory mode implementation
- `pipeline.py` - Core agent workflow and LLM integration
- `prompts.py` - Agent persona templates (based on Huang & Yang 2025)
- `config.yaml` - Central configuration for LLM and pipeline parameters
- `utils.py` - Helper functions for file operations

### Configuration (`config.yaml`)

```yaml
# Key settings:
problem_id: 'asml'                    # Problem to solve
model_name: 'gemini-2.5-pro'          # LLM model
temperature: 0.1                      # For consistent reasoning
max_correction_loops: 125             # Max verification iterations
final_verification_passes: 4          # Final check passes
enable_parallelization: true          # Parallel processing
parallel_trajectory_mode: true        # Multiple solution paths
```

### Pipeline Features

- **Checkpoint/Resume**: Automatic checkpoint saving after each stage
- **Parallel Processing**: Initial generation and final verification can run in parallel
- **Parallel Trajectories**: Each initial sample runs through entire pipeline independently
- **Streaming Support**: OpenAI endpoint supports streaming to prevent timeouts
- **XML-Structured Output**: Solutions use `<answer>`, `<solution>`, `<reflection>` tags
- **LaTeX Support**: Mathematical notation within $ delimiters

### Adding New Problems

1. Create `.md` file in `solver/problems/` with LaTeX math
2. Update `problem_id` in `config.yaml`
3. Run: `cd solver && python -m solver.main`
4. Outputs saved to `solver/outputs/{problem_id}/`

### LLM Integration Status

The `call_llm()` function in `pipeline.py` requires implementation with actual API calls (supports both Gemini and OpenAI endpoints).

## Development Notes

- Python 3.11+ required (see `solver/.python-version`)
- No external dependencies currently (update `solver/pyproject.toml` as needed)
- No linting/formatting tools configured yet
- Tests use standard pytest when available

## Agent Development Kit (ADK) Documentation (`/adk-docs`)

### Overview
Contains comprehensive documentation and examples for Google's Agent Development Kit - an open-source, code-first toolkit for building, evaluating, and deploying AI agents. While optimized for Gemini and Google ecosystem, ADK is model-agnostic and deployment-agnostic.

### Key Features
- **Rich Tool Ecosystem**: Pre-built tools, custom functions, OpenAPI specs integration
- **Code-First Development**: Define agent logic in Python and Java
- **Modular Multi-Agent Systems**: Compose specialized agents into hierarchies
- **Built-in Observability**: Tracing and monitoring with AgentOps support
- **Deploy Anywhere**: Cloud Run or Vertex AI Agent Engine deployment

### Directory Structure
```
adk-docs/
├── docs/                    # MkDocs documentation source
│   ├── agents/             # Agent types and patterns
│   ├── tools/              # Tool integration guides
│   ├── get-started/        # Quickstart guides
│   ├── streaming/          # Real-time streaming setup
│   └── deploy/             # Deployment strategies
├── examples/               # Code samples
│   ├── python/            # Python implementations
│   └── java/              # Java implementations
└── site/                  # Generated documentation site
```

### Common ADK Development Commands
```bash
# Navigate to examples
cd adk-docs/examples/python

# Install ADK for Python development
pip install google-adk

# Run example agents
python snippets/get-started/google_search_agent/agent.py

# Build documentation site
cd adk-docs
mkdocs serve
```

### Agent Types Available
- **LLM Agents**: Basic single-turn agents with tool integration
- **Loop Agents**: Multi-turn conversation agents
- **Sequential Agents**: Step-by-step workflow execution
- **Parallel Agents**: Concurrent task execution
- **Custom Agents**: Fully customizable agent implementations

### Integration Points
- **Google Cloud Tools**: BigQuery, Vertex AI Search, Google Search
- **Third-party Tools**: LangChain, CrewAI integration examples
- **Authentication**: OAuth and service account patterns
- **Streaming**: WebSocket and HTTP streaming implementations


## Project Notes

### Important Testing Considerations
- When testing with `gemini-2.5-pro`, ensure comprehensive coverage across various use cases
- The application supports multiple database backends (MySQL/SQLite)
- Configuration changes through the UI take effect immediately
- Failed API keys are automatically rotated and can be re-enabled after the check interval

## Department of Market Intelligence (DoMI) Project

### Overview
DoMI is a sophisticated multi-agent research system using Google ADK for quantitative market analysis. It orchestrates multiple specialized agents through a context-aware workflow to conduct comprehensive financial research with proper validation and execution tracking.

### Architecture
- **Root Workflow**: Orchestrates the entire research pipeline with context-aware validation
- **Planning Phase**: Chief Researcher creates research plans with multi-tier validation
- **Implementation Phase**: Orchestrator decomposes plans into parallel execution graphs
- **Execution Phase**: Experiment Executor runs code with detailed journaling
- **Validation System**: Context-aware validators provide specialized feedback

### Directory Structure
```
department_of_market_intelligence/
├── agents/              # Agent implementations (one file per agent type)
├── workflows/           # Workflow orchestration logic
├── tools/               # Tool implementations (MCP, mock tools)
├── utils/               # Shared utilities (state management, model loading)
├── tasks/               # Research task definitions (.md files)
├── outputs/             # Generated outputs by task ID
├── checkpoints/         # Workflow checkpoints for recovery
├── tests/               # All tests (no root level test files)
├── prompts/             # Centralized prompt templates (TO BE CREATED)
└── config.py            # Central configuration
```

### Common Development Commands
```bash
# Run the main research pipeline
python -m department_of_market_intelligence.main

# Run with specific task
TASK_ID=my_research_task python -m department_of_market_intelligence.main

# Run in dry run mode (no LLM calls)
# Edit config.py: DRY_RUN_MODE = True

# Resume from checkpoint
python -m department_of_market_intelligence.main --resume

# View checkpoint status
python checkpoint_cli.py status
```

## Code Conventions - CRITICAL

### 1. Prompt Management
```python
# ❌ BAD - Inline prompts
instruction="""
Your prompt here...
"""

# ✅ GOOD - Use constants
AGENT_NAME_INSTRUCTION = """
Your prompt here...
"""
# Then use: instruction=AGENT_NAME_INSTRUCTION
```

### 2. Communication Protocol
All agents MUST follow this protocol:
```
### COMMUNICATION PROTOCOL - CRITICAL ###
ALWAYS start your response with:
🤔 [AgentName]: Examining the session state to understand what's needed...

Then EXPLICITLY mention:
- 📁 Working directory: {outputs_dir}
- 📖 Reading from: [specific file paths]
- 💾 Writing to: [specific file paths] 
- 🎯 Current task: {current_task}
```

### 3. File Organization
- **One implementation per concept** - No `validators_v2.py`, `validators_updated.py`
- **Consolidate, don't duplicate** - Refactor existing code instead of creating variants
- **Remove dead code immediately** - No abandoned implementations
- **Debug scripts go in dev tools** - Not in production codebase

### 4. Path Handling
```python
# ❌ BAD - Hardcoded paths
path = "/home/gaen/agents_gaen/department_of_market_intelligence/outputs/task/file.md"

# ✅ GOOD - Use config variables
path = f"{outputs_dir}/planning/research_plan_v{version}.md"
```

### 5. Test Organization
- All tests in `tests/` directory
- Clear naming: `test_<feature>.py`
- No root-level test files
- Clean up test outputs after runs

### 6. State Management
- Use Pydantic `SessionState` model for type safety
- Follow artifact-pointer pattern (store paths, not data)
- Validate state transitions
- Use `StateAdapter` for backward compatibility

### 7. Agent Creation Pattern
```python
# Use agent factory for async initialization
from agents.agent_factory import get_chief_researcher_agent_async

# In async context:
agent = await get_chief_researcher_agent_async()
```

## Refactoring Guidelines

### When Adding Features
1. Check if similar code exists - consolidate instead of duplicating
2. Update existing files rather than creating new versions
3. Remove old implementations after successful refactoring
4. Update tests to match new implementation

### Validator Consolidation Plan
Current mess: `validators.py`, `validators_updated.py`, `validators_enhanced.py`, `validators_context_aware.py`
Target: Single `validators.py` with context-aware support

### Prompt System Refactoring
1. Create `prompts/` directory
2. Move all prompt constants to centralized files
3. Create base templates for common patterns
4. Import prompts in agent files

## Critical Configuration

### Custom Endpoint Setup
- **Token**: `sk-7m-daily-token-1` for custom endpoint
- **Endpoint**: `0.0.0.0:10000` (gemini-balance server)
- **Format**: OpenAI-compatible (keep this, don't change to Gemini format)

### Model Configuration
- All agents use `gemini-2.5-pro`
- 10-minute timeout for thinking tokens
- MCP timeout: 180 seconds (3 minutes)

### Micro-Checkpoint Configuration
Fine-grained operation recovery is now available through config.py:

```python
# Enable/disable micro-checkpoints for sub-operation recovery
ENABLE_MICRO_CHECKPOINTS = True

# Auto-resume incomplete operations on startup
MICRO_CHECKPOINT_AUTO_RESUME = True

# Max retries per failed operation step
MICRO_CHECKPOINT_MAX_RETRIES = 3

# Timeout per operation step (seconds)
MICRO_CHECKPOINT_TIMEOUT = 300

# Days to keep completed operation checkpoints
MICRO_CHECKPOINT_CLEANUP_DAYS = 7
```

Environment variables supported:
```bash
export ENABLE_MICRO_CHECKPOINTS=true
export MICRO_CHECKPOINT_AUTO_RESUME=true  
export MICRO_CHECKPOINT_MAX_RETRIES=3
export MICRO_CHECKPOINT_TIMEOUT=300
export MICRO_CHECKPOINT_CLEANUP_DAYS=7
```

### Task Loading
- Tasks loaded from `tasks/` directory
- Task ID maps to `{task_id}.md` file
- Outputs go to `outputs/{task_id}/`
- Follow solver's explicit loading pattern

## API Integration Notes
- **CRITICAL**: Keep OpenAI format even though using Gemini endpoint
- Use `StreamingLiteLlm` wrapper for all LLM calls
- Handle thinking tokens with extended timeouts
- Respect `DRY_RUN_MODE` for testing without LLM calls

## Command Line Memories

- Run DoMI: `python -m department_of_market_intelligence.main`
- Custom endpoint uses port 10000, not 8000
- Always check `DRY_RUN_MODE` setting in config.py
- When you want to run department_of_market_intelligence.main, you have to: cd to /home/gaen/agents_gaen and then you'll run python -m department_of_market_intelligence.main

## Common Pitfalls to Avoid

### 1. Creating Duplicate Implementations
❌ **DON'T**: Create `agent_v2.py` when fixing bugs
✅ **DO**: Fix the existing `agent.py` file

### 2. Hardcoding Paths in Prompts
❌ **DON'T**: `/home/gaen/agents_gaen/department_of_market_intelligence/outputs/{task_id}/`
✅ **DO**: Use `{outputs_dir}` variable that's passed to prompts

### 3. Mixing Test and Production Code
❌ **DON'T**: Leave debug scripts in root directory
✅ **DO**: Move to `dev_tools/` or remove entirely

### 4. Ignoring Existing Patterns
❌ **DON'T**: Create your own state management
✅ **DO**: Use existing `SessionState` and `StateAdapter`

### 5. Committing Generated Outputs
❌ **DON'T**: Commit checkpoint outputs to git
✅ **DO**: Add to `.gitignore` and clean regularly

## Quick Reference

### Key Variables Available in Prompts
- `{task_id}` - Current task identifier
- `{outputs_dir}` - Task-specific output directory
- `{current_task}` - Current workflow task
- `{current_date}` - Today's date
- `{plan_version}` - Current plan version number
- `{task_file_path}` - Path to task description

### Workflow Task Names
Planning Phase:
- `generate_initial_plan`
- `refine_plan`

Implementation Phase:
- `generate_implementation_plan`
- `generate_results_extraction_plan`

Execution Phase:
- `execute_experiments`
- `extract_results`

Final Phase:
- `generate_final_report`

### Project Philosophy
1. **Explicit over Implicit** - Clear task loading, obvious file paths
2. **Type Safety** - Pydantic models over dictionaries
3. **Fail Fast** - Validate early, clear error messages
4. **Clean Architecture** - Separation of concerns, single responsibility
5. **Maintainability** - One way to do things, clear conventions

## Command Line Memories

- remember to read department_of_market_intelligence/centralized_prompt_construction_blueprint.md after doing compact
# Repository Guidelines

## Project Structure & Module Organization
- `department_of_market_intelligence/` hosts the ULTRATHINK quantitative research stack, with `agents/`, `tasks/`, `workflows/`, and rich validation assets under `tests/` and `prompts/`.
- `solver/` contains the IMO solver pipeline (`main.py`, `pipeline.py`, `problems/`, `outputs/`) plus supporting config and verification scripts.
- `adk-docs/` packages Gemini ADK documentation and runnable samples; use it as a reference for agent integrations and tool APIs.
- Root-level scripts such as `test_multi_tool_calls_adk.py` and `debug_multiple_tool_calls.py` provide quick smoke tests for ADK tool orchestration.

## Build, Test, and Development Commands
- `python -m department_of_market_intelligence.main` runs the end-to-end research workflow using `config.py` and the checkpoint system.
- `python -m solver.main` executes the IMO solver with resume-aware verification passes defined in `config.yaml`.
- `python department_of_market_intelligence/tests/run_all_tests.py` orchestrates the curated regression suite; watch its output for timing and failure summaries.
- Targeted checks: `python -m department_of_market_intelligence.tests.test_session_state` exercises state models, while `python solver/test_parallel_trajectories.py` stress-tests concurrency.
- For ADK examples, install sample requirements and run from `adk-docs/examples/python/...` as documented in each subfolder.

## Coding Style & Naming Conventions
- Follow Python 3.11 conventions: 4-space indentation, type hints, and explicit dataclasses/Pydantic models for shared state.
- Keep module filenames in `snake_case`, class names in `PascalCase`, and configuration artifacts in YAML or JSON with lowercase keys.
- Retain structured logging/print markers used for timeline tracing—tests expect them when parsing outputs.

## Testing Guidelines
- Place new tests under `department_of_market_intelligence/tests/` or `solver/` with the `test_<feature>.py` pattern; prefer deterministic seeds when randomness is required.
- Extend `run_all_tests.py` when adding suites so they remain part of the regression loop.
- Document any external service mocks or fixtures inside `tests/utils/` to keep workflows reproducible.

## Commit & Pull Request Guidelines
- Write imperative, subsystem-scoped commit messages (e.g., `Add context-aware validator metrics`).
- Each PR should summarize functional changes, list the test commands you ran, flag config updates, and link relevant issues or design docs.
- Include before/after evidence (logs, screenshots) when altering agent behavior or generated artifacts.

## System Notes Reference
- The `~/Documents/system_notes/` folder is operationally important; expect to see `shell_maintenance.md` outlining shared Bash/Zsh startup ordering and alias sources. Review it before editing shell-dependent tooling so agent scripts keep loading the intended environment.

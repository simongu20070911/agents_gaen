# Development Workflow

## Environment setup

1. Install Python 3.11 (all pipelines assume 3.11-specific features).
2. Create a virtual environment: `python -m venv .venv && source .venv/bin/activate`.
3. Install dependencies as documented within each sub-project:
   - Consult `department_of_market_intelligence/docs/` for ULTRATHINK setup notes.
   - Review the guides in `solver/` for solver-specific requirements.
   - Follow `adk-docs/` instructions for Gemini ADK samples.
4. Review shell customisations in `~/Documents/system_notes/shell_maintenance.md` before modifying shell tooling that agents depend on.

## Core commands

- Run the ULTRATHINK end-to-end research workflow:
  ```bash
  python -m department_of_market_intelligence.main
  ```
- Execute the IMO solver pipeline:
  ```bash
  python -m solver.main
  ```
- Regression suite for ULTRATHINK:
  ```bash
  python department_of_market_intelligence/tests/run_all_tests.py
  ```
- Targeted checks:
  - `python -m department_of_market_intelligence.tests.test_session_state`
  - `python solver/test_parallel_trajectories.py`
- ADK smoke tests:
  - `python test_multi_tool_calls_adk.py`
  - `python debug_multiple_tool_calls.py`

## Coding standards

- 4-space indentation, explicit type hints, and dataclasses/Pydantic for shared state.
- Keep module filenames in `snake_case`, classes in `PascalCase`, configuration keys in lower-case YAML/JSON.
- Preserve structured logging markers used by regression tooling.
- Prefer deterministic seeds when randomness is involved; document fixtures under `tests/utils/`.

## Contributions & testing

- Add new tests under `department_of_market_intelligence/tests/` or `solver/` with files named `test_<feature>.py`.
- Extend `department_of_market_intelligence/tests/run_all_tests.py` when you introduce new suites.
- For PRs, include: summary of functional changes, list of test commands executed, any config updates, and links to relevant design docs or issues.
- Capture before/after artefacts (logs, screenshots) when altering agent behaviour or generated outputs.

# Agents Gaen Research Stack

This workspace hosts multiple agentic research pipelines, simulation scripts, and documentation used for market intelligence experiments. The project combines the ULTRATHINK research stack, an IMO solver workflow, and ADK-driven samples under a single repository.

## Repository layout

- `department_of_market_intelligence/` – ULTRATHINK quantitative research stack with production agents, prompts, workflows, and regression assets.
- `solver/` – IMO solver pipeline with configurable trajectories, outputs, and verification utilities.
- `adk-docs/` – Gemini ADK documentation, runnable examples, and integration notes.
- `docs/` – Curated documentation added for discoverability, including onboarding guides and reference indices.
- Root helper scripts (`test_multi_tool_calls_adk.py`, `debug_multiple_tool_calls.py`, etc.) – Quick smoke tests for tool orchestration.
- `draft_folder/`, `data/`, and other scratch directories – Convenience workspaces that stay untracked thanks to `.gitignore`.

## Getting started

1. **Clone dependencies** – Submodules (`department_of_market_intelligence`, `solver`, `adk-docs`, etc.) already contain their own `.git` metadata. If you cloned with `--recurse-submodules`, they come pre-populated.
2. **Install Python 3.11** – All runtime scripts target Python 3.11 with type hints and dataclasses.
3. **Set up a virtual environment** – `python -m venv .venv && source .venv/bin/activate`.
4. **Install dependencies** – Follow instructions in each sub-project (`department_of_market_intelligence/docs/`, `solver/README.md`, `adk-docs/README.md`).
5. **Run key workflows**:
   - `python -m department_of_market_intelligence.main`
   - `python -m solver.main`
   - `python department_of_market_intelligence/tests/run_all_tests.py`

## Documentation

Additional curated documentation, including architecture notes and workflow walkthroughs, now lives under `docs/`. See `docs/README.md` for a full index, plus cross-links into `department_of_market_intelligence/docs/` and `adk-docs/`.

## Contributing

- Follow Python 3.11 conventions: four-space indentation, explicit typing, and dataclass/Pydantic models for shared state.
- Keep module filenames in `snake_case`, class names in `PascalCase`, and configs in lower-case YAML/JSON.
- Structured logs and timeline markers are required for regression tooling—retain any existing print markers.
- Before opening a PR, list the tests you ran and provide before/after artefacts when behaviour changes.

For deeper subsystem notes, refer to `docs/development.md` or per-project documentation.

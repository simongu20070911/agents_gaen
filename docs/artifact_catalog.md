# Artifact Catalog

This catalog describes the notable directories and files so contributors can quickly locate resources.

## Directories

- `adk-docs/` – Gemini ADK documentation, examples, and site assets.
- `department_of_market_intelligence/` – ULTRATHINK research stack:
  - `agents/` – Agent definitions and behaviour specifications.
  - `tasks/` – Task templates and execution logic.
  - `workflows/` – End-to-end orchestration pipelines.
  - `prompts/` – Prompt libraries used by agents.
  - `tests/` – Regression and unit test suites.
  - `docs/` – Subsystem-specific documentation.
  - `outputs/` – Generated artefacts (ignored by Git).
- `solver/` – IMO solver project:
  - `problems/` – Problem definitions and datasets.
  - `outputs/` – Generated solutions (ignored by Git).
  - `pipeline.py` / `main.py` – Entry points for solver execution.
- `draft_folder/`, `data/`, `nate-container/` – Scratch or local-only workspaces excluded from version control.
- `.history/` – Editor history metadata (ignored).

## Key files

- `README.md` – Top-level overview and onboarding instructions.
- `docs/` – Centralised documentation hub (this folder).
- `AGENTS.md`, `CLAUDE.md`, `adk_txt_documentary.txt`, `dmoi.txt`, `dmoivision.txt` – Reference notes retained for legacy context.
- `test_multi_tool_calls_adk.py`, `test_llm_multiple_tool_calls.py`, `test_validation_loop.py`, `debug_multiple_tool_calls.py` – Smoke test scripts.
- `copy_dmoi_essential_structure.sh` – Script to replicate the essential ULTRATHINK directory layout.

Update this catalog when introducing new major modules, auxiliary scripts, or documentation bundles.

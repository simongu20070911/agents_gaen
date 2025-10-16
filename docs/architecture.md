# Architecture Overview

## Top-level systems

- **ULTRATHINK (department_of_market_intelligence/)**  
  Provides multi-agent quantitative research workflows. Agents, tasks, prompts, and validation assets live under dedicated subdirectories. `main.py` orchestrates an end-to-end research session using `config.py` and checkpointing within `checkpoints/`.

- **IMO Solver (solver/)**  
  Offers a pipeline for mathematical problem solving with resume-aware verification. `pipeline.py` and `main.py` coordinate workloads across `problems/` and persist artefacts under `outputs/`.

- **Gemini ADK Samples (adk-docs/)**  
  Houses documentation and runnable examples for Gemini ADK integrations. Refer to the `examples/python/` subfolders for reference agent/tool usage patterns.

## Shared assets & scripts

- Root-level scripts (`test_multi_tool_calls_adk.py`, `debug_multiple_tool_calls.py`, `test_validation_loop.py`) enable quick smoke tests of tool orchestration and validation scenarios.
- `copy_dmoi_essential_structure.sh` reproduces the core layout for ULTRATHINK components.
- `AGENTS.md`, `CLAUDE.md`, and related text files capture historical context and personas leveraged across experiments.

## Data & outputs

- `department_of_market_intelligence/outputs/` and `solver/outputs/` collect generated artefacts. These directories are ignored by Git to keep the repository lean.
- Scratch workspaces such as `data/` and `draft_folder/` reside at the root for exploratory work and are also ignored.

## Testing & validation

- Regression coverage resides under `department_of_market_intelligence/tests/`, supported by prompts in `prompts/` and workflows under `workflows/`.
- Solver-specific tests live directly within `solver/`.
- Structured logging is critical; maintain existing markers to ensure parsing by `run_all_tests.py` and solver verification scripts.

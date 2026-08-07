# Repository Map

This file explains what each folder and major file in the repo does.

## Root Files

- `README.md` - top-level project summary and quick start.
- `pyproject.toml` - Python package metadata and entry points.
- `.env.example` - sample environment variables.
- `.gitignore` - ignores local build, cache, and environment files.

## `configs/`

- `app.yaml` - app-level configuration defaults.
- `evals.yaml` - evaluation settings.
- `policies.yaml` - governance and policy defaults.
- `prompts.yaml` - prompt templates used by the LLM helpers.

## `data/`

### `data/synthetic/`

- `customers.json` - synthetic customer master data.
- `events.json` - merged event store used by the pipeline.
- `goldens.json` - scenario definitions and expected outcomes.
- `sources/` - split source exports such as web, app, support, payments, communications, and surveys.
- `README.md` - explanation of the synthetic data layout.

### `data/processed/`

- `renewal_risk_demo.json` - example processed output for the showcase.
- `README.md` - what generated outputs belong here.

### `data/goldens/`

- `README.md` - notes about golden evaluation cases and expected behavior.

## `docs/`

- `PIPELINE.md` - step-by-step explanation of the runtime pipeline.
- `ARCHITECTURE_FLOW.md` - architecture diagram and layer breakdown.
- `UI_GUIDE.md` - how the dashboard works and how to explain it.
- `REPO_MAP.md` - this file.
- `ARCHITECTURE.md` - high-level architecture overview.
- `DATA_STRATEGY.md` - how the synthetic data is organized.
- `ENVIRONMENT_SETUP.md` - environment and run instructions.

## `scripts/`

- `generate_synthetic_data.py` - generate or refresh the synthetic dataset.
- `run_demo.py` - run the demo from the command line.
- `run_evals.py` - run the evaluation suite.
- `run_api.py` - launch the FastAPI server and dashboard.
- `_bootstrap.py` - helper for local imports and script startup.
- `README.md` - script overview.

## `src/cx_agent/`

### Core Models and Settings

- `models.py` - dataclasses for customers, events, journeys, recommendations, gates, audit entries, and judge output.
- `settings.py` - environment-driven configuration loader.
- `__init__.py` - marks the package.

### `src/cx_agent/ingestion/`

- `files.py` - read/write JSON, load customers and events, split events by source bucket.
- `synthetic.py` - create the synthetic customer and event dataset.
- `__init__.py` - package marker.

### `src/cx_agent/journeys/`

- `builder.py` - sort events into a timeline and infer journey stage and friction.
- `__init__.py` - package marker.

### `src/cx_agent/personalization/`

- `profile.py` - build a compact customer profile from recent behavior.
- `__init__.py` - package marker.

### `src/cx_agent/agents/`

- `recommendations.py` - choose the next best action from the journey and profile.
- `__init__.py` - package marker.

### `src/cx_agent/guardrails/`

- `verification.py` - ownership, capability, and PII masking rules.
- `__init__.py` - package marker.

### `src/cx_agent/llm/`

- `openrouter.py` - optional OpenRouter-based explanation and judge commentary.
- `__init__.py` - package marker.

### `src/cx_agent/evals/`

- `golden.py` - compare output against golden expectations.
- `judge.py` - score the demo output and optionally ask the LLM for commentary.
- `__init__.py` - package marker.

### `src/cx_agent/orchestration/`

- `graph.py` - LangGraph workflow for the demo run.
- `pipeline.py` - helper functions for demos, analytics, judge review, and presentation bundles.
- `__init__.py` - package marker.

### `src/cx_agent/api/`

- `app.py` - FastAPI application, routes, and static UI hosting.
- `models.py` - API response schemas.
- `static/index.html` - dashboard shell.
- `static/styles.css` - dashboard styling.
- `static/app.js` - dashboard behavior and rendering logic.
- `__init__.py` - package marker.

### Other Package Folders

- `src/cx_agent/cli/main.py` - CLI entry point and commands.
- `src/cx_agent/identity/` - removed unused placeholder package.
- `src/cx_agent/storage/` - removed unused placeholder package.
- `src/cx_agent/utils/` - removed unused placeholder package.

## `tests/`

- `unit/README.md` - unit-test notes.
- `integration/README.md` - integration-test notes.
- `golden/README.md` - golden-case testing notes.

## What Was Cleaned Up

- temporary build folders under `.tmp/`,
- Python cache folders,
- generated packaging metadata under `src/cx_agent.egg-info/`,
- unused placeholder package folders.

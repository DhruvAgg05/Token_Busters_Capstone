# Files And Folders

This guide matches the current repo tree exactly.

## Root

- `README.md` - short project overview and quick start.
- `pyproject.toml` - Python package metadata and CLI entry points.
- `.env.example` - sample environment variables for local setup.

## `data/`

### `data/synthetic/`

- `customers.json` - customer master data.
- `events.json` - merged event timeline used by the pipeline.
- `goldens.json` - scenario definitions for demo and eval.
- `sources/` - split source exports for source-by-source storytelling.
- `sources/README.md` - short note about the source-split dataset layout.

### `data/processed/`

- `renewal_risk_demo.json` - example generated output from a demo run.

## `docs/`

These are supporting walkthrough files.

- `ARCHITECTURE_FLOW.md` - architecture diagram and layer breakdown.
- `PIPELINE.md` - step-by-step runtime flow.
- `REPO_MAP.md` - repo map.
- `UI_GUIDE.md` - how to explain the dashboard to judges.

## `explanation/`

This is the judge-facing source of truth.

- `README.md` - entry page for the explanation set.
- `PIPELINE.md` - complete pipeline explanation.
- `ARCHITECTURE.md` - flowchart and architecture breakdown.
- `FILES_AND_FOLDERS.md` - current folder and file guide.

## `scripts/`

- `generate_synthetic_data.py` - create or refresh the synthetic dataset.
- `run_demo.py` - run the terminal demo.
- `run_evals.py` - run the eval suite.
- `run_api.py` - start the FastAPI app and dashboard.
- `_bootstrap.py` - helper for local imports when scripts run directly.

## `src/cx_agent/`

This is the application code.

### Core files

- `models.py` - dataclasses for customers, events, journeys, recommendations, gates, audits, and judge results.
- `settings.py` - environment-based configuration loader.

### `src/cx_agent/ingestion/`

- `files.py` - JSON read/write, source splitting, and data loading.
- `synthetic.py` - generates the synthetic dataset.

### `src/cx_agent/journeys/`

- `builder.py` - builds timelines and infers journey stages.

### `src/cx_agent/personalization/`

- `profile.py` - creates the customer profile used for personalization.

### `src/cx_agent/agents/`

- `recommendations.py` - chooses the next best action.

### `src/cx_agent/guardrails/`

- `verification.py` - ownership, capability, and masking rules.

### `src/cx_agent/llm/`

- `openrouter.py` - optional LLM explanation and judge commentary.

### `src/cx_agent/evals/`

- `golden.py` - compares output to golden expectations.
- `judge.py` - scores the output like a reviewer would.

### `src/cx_agent/orchestration/`

- `graph.py` - LangGraph workflow for the demo pipeline.
- `pipeline.py` - helper functions for demo runs, analytics, judging, and presentation bundles.

### `src/cx_agent/api/`

- `app.py` - FastAPI routes and UI hosting.
- `models.py` - API response schemas.
- `static/index.html` - dashboard layout.
- `static/styles.css` - dashboard styling.
- `static/app.js` - dashboard behavior.

### `src/cx_agent/cli/`

- `main.py` - CLI commands for demo, evals, analytics, judge, and presentation.

## `UI_SC/`

This folder contains the screenshot sequence for explaining the UI to judges.

- `1.png` - landing and executive summary.
- `2.png` - control center and customer story.
- `3.png` - journey, evidence, and gates.
- `4.png` - CX analytics and audit trail.
- `5.png` - audit trail details.

## What Changed

- Removed placeholder folders that are no longer part of the showcase.
- Removed cache files and generated package metadata.
- Kept only the current runtime files, the dataset, the dashboard UI, and the explanation pack.

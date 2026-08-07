# Repository Map

This file reflects the current repo tree. The `explanation/` folder is the primary judge-facing guide.

## Root Files

- `README.md` - top-level project summary and quick start.
- `pyproject.toml` - Python package metadata and CLI entry points.
- `.env.example` - sample environment variables.

## `data/`

### `data/synthetic/`

- `customers.json` - synthetic customer master data.
- `events.json` - merged event store used by the pipeline.
- `goldens.json` - scenario definitions and expected outcomes.
- `sources/` - split source exports such as web, app, support, payments, communications, and surveys.
- `sources/README.md` - short note about the source-split dataset layout.

### `data/processed/`

- `renewal_risk_demo.json` - example processed output for the showcase.
- `audit_runs/` - auto-generated JSON artifacts for each demo run.

## `docs/`

These files are supporting notes.

- `PIPELINE.md` - step-by-step explanation of the runtime pipeline.
- `ARCHITECTURE_FLOW.md` - architecture diagram and layer breakdown.
- `UI_GUIDE.md` - how the dashboard works and how to explain it.
- `REPO_MAP.md` - this file.

## `explanation/`

This is the judge-facing explanation pack.

- `README.md` - entry page for the explanation set.
- `PIPELINE.md` - complete pipeline explanation.
- `ARCHITECTURE.md` - flowchart and architecture breakdown.
- `FILES_AND_FOLDERS.md` - current folder and file guide.

## `scripts/`

- `generate_synthetic_data.py` - generate or refresh the synthetic dataset.
- `run_demo.py` - run the demo from the command line.
- `run_evals.py` - run the evaluation suite.
- `run_api.py` - launch the FastAPI server and dashboard.
- `_bootstrap.py` - helper for local imports and script startup.

## `src/cx_agent/`

### Core Files

- `models.py` - dataclasses for customers, events, journeys, recommendations, gates, audits, and judge output.
- `settings.py` - environment-driven configuration loader.

### `src/cx_agent/ingestion/`

- `files.py` - read/write JSON, load customers and events, split events by source bucket.
- `synthetic.py` - create the synthetic customer and event dataset.

### `src/cx_agent/journeys/`

- `builder.py` - sort events into a timeline and infer journey stage and friction.

### `src/cx_agent/personalization/`

- `profile.py` - build a compact customer profile from recent behavior.

### `src/cx_agent/agents/`

- `recommendations.py` - choose the next best action from the journey and profile.

### `src/cx_agent/guardrails/`

- `verification.py` - ownership, capability, and PII masking rules.

### `src/cx_agent/llm/`

- `openrouter.py` - optional OpenRouter-based explanation and judge commentary.

### `src/cx_agent/evals/`

- `golden.py` - compare output against golden expectations.
- `judge.py` - score the demo output and optionally ask the LLM for commentary.

### `src/cx_agent/orchestration/`

- `graph.py` - LangGraph workflow for the demo run.
- `pipeline.py` - helper functions for demos, analytics, judge review, and presentation bundles.

### `src/cx_agent/api/`

- `app.py` - FastAPI application, routes, and static UI hosting.
- `models.py` - API response schemas.
- `static/index.html` - dashboard shell.
- `static/styles.css` - dashboard styling.
- `static/app.js` - dashboard behavior and rendering logic.

### `src/cx_agent/cli/`

- `main.py` - CLI entry point and commands.

## `UI_SC/`

This folder contains the screenshot sequence for explaining the UI to judges.

- `1.png` - landing and executive summary.
- `2.png` - control center and customer story.
- `3.png` - journey, evidence, and gates.
- `4.png` - CX analytics and audit trail.
- `5.png` - audit trail details.

## What Was Cleaned Up

- placeholder folders that are no longer part of the showcase,
- cache folders,
- generated packaging metadata,
- old raw-data placeholders.

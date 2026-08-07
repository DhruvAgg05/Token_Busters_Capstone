# Personalized AI-Driven Customer Journey Mapping

Backend-first agentic CX MVP for turning scattered customer signals into one governed journey view.

## Quick Docs

- `explanation/README.md` - start here for the full project explanation pack
- `explanation/PIPELINE.md` - how the whole system works
- `explanation/ARCHITECTURE.md` - architecture and flowchart
- `explanation/FILES_AND_FOLDERS.md` - what each folder and file does

## What It Does

The system:

- takes customer signals from multiple source files,
- merges them into one unified event timeline,
- detects friction points,
- predicts the likely risk or opportunity,
- recommends the next best action,
- checks ownership and capability rules,
- produces an auditable, masked result.

## Current Data Flow

```text
Synthetic source files
    |
    v
Source merge + normalization
    |
    v
Unified customer events
    |
    v
Journey analysis + profile building
    |
    v
Recommendation + guardrails + evals
    |
    v
CLI / API output
```

## What Is In The Repo

- `data/synthetic/customers.json` for customer master records
- `data/synthetic/sources/*.json` for split synthetic source exports
- `data/synthetic/events.json` for the merged unified event store
- `data/synthetic/goldens.json` for evaluation scenarios
- `data/processed/` for generated demo outputs
- `src/cx_agent/` for ingestion, journey logic, recommendations, guardrails, evals, CLI, API, and dashboard assets
- `docs/` for supporting notes and walkthroughs
- `explanation/` for the judge-facing pipeline, architecture, UI, and repo guide

## What We Have Done

- built a synthetic multi-source dataset,
- added source-level split files and a merge step,
- implemented journey reconstruction through a LangGraph workflow,
- implemented friction detection,
- implemented profile building and recommendations,
- implemented ownership and capability gates,
- added golden-case evals,
- added an audit trail for each demo run,
- added CX analytics summaries,
- added a judge-style quality score for demo outputs,
- added source provenance in the audit trail,
- added a final judge presentation command,
- added a browser-based dashboard,
- exposed CLI and API demo flows.

## What Is Left

- expand the dataset further with more scenarios and edge cases,
- add more golden cases,
- add stronger tests for merge, guardrail, and blocked-action paths,
- add more audit-log style output if needed for the judge story.

## Run It

```bash
python -m pip install -e .
cx-agent generate-data
cx-agent list-scenarios --verbose
cx-agent demo --scenario renewal_risk --role customer_success_manager --region US
cx-agent evals --show-details
cx-agent analytics --show-details
cx-agent judge --scenario renewal_risk --role customer_success_manager --region US
cx-agent presentation --scenario renewal_risk --role customer_success_manager --region US
cx-agent demo --scenario onboarding_payment_help --role customer_success_manager --region IN
python scripts/run_api.py
```

Open the dashboard at `http://127.0.0.1:8000/ui` after starting the API.

## Judge-Friendly Summary

This project is an agentic CX intelligence layer that collects customer signals from multiple touchpoints, unifies them into one journey, identifies the main problem, recommends the next best action, and blocks unsafe actions when the user is not allowed to act.

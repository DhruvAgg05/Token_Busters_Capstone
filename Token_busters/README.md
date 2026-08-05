# Personalized AI-Driven Customer Journey Mapping

Backend-first hackathon scaffold for an Agentic CX Intelligence platform.

## Goal

Build a command-line MVP that:

- ingests customer interaction data from multiple touchpoints,
- creates a unified customer journey,
- detects friction points,
- predicts likely next outcomes,
- recommends secure next-best actions,
- applies basic guardrails, evaluation gates, and ownership/capability checks.

This repo is intentionally backend-first so the team can demonstrate the intelligence layer before investing in a frontend.

## Environment Setup

Copy `.env.example` to `.env` and fill in the required values.

See [ENVIRONMENT_SETUP.md](D:\EXL\Capstone\Token_busters\docs\ENVIRONMENT_SETUP.md) for the full key list and which ones are required now.

## MVP Scope

For the hackathon, the system should run from the command line and demonstrate:

1. Data ingestion from synthetic multi-channel customer data
2. Identity resolution and unified customer timeline creation
3. Journey stage mapping
4. Friction detection
5. Personalization and next-best-action generation
6. Guardrailed response generation with verification gates
7. Offline evals using golden test cases

## Recommended Repo Structure

```text
Token_busters/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_STRATEGY.md
│   └── IMPLEMENTATION_PLAN.md
├── data/
│   ├── raw/
│   ├── synthetic/
│   ├── processed/
│   └── goldens/
├── configs/
│   ├── app.yaml
│   ├── prompts.yaml
│   ├── policies.yaml
│   └── evals.yaml
├── src/
│   └── cx_agent/
│       ├── cli/
│       ├── ingestion/
│       ├── identity/
│       ├── journeys/
│       ├── agents/
│       ├── personalization/
│       ├── guardrails/
│       ├── evals/
│       ├── orchestration/
│       ├── storage/
│       └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── golden/
└── scripts/
    ├── generate_synthetic_data.py
    ├── run_demo.py
    └── run_evals.py
```

## Core Concepts We Should Apply

### 1. Personalization

- Build a lightweight customer profile from interactions, preferences, issues, segment, sentiment, and recent activity.
- Use profile context when generating next-best actions.
- Keep personalization policy-driven so the system avoids overreaching or using sensitive fields improperly.

### 2. Golden Datasets

- Maintain a small set of trusted examples in `data/goldens/`.
- Each golden case should include:
  - input events,
  - expected journey stage,
  - expected friction label,
  - expected risk or recommendation category,
  - expected safe-response behavior.

### 3. Eval Gate

- Every major build/demo run should pass core evals before being shown.
- Example gates:
  - journey reconstruction accuracy,
  - friction classification consistency,
  - recommendation relevance,
  - policy compliance,
  - hallucination check on secure responses.

### 4. Two-Gate Verification

- Ownership gate:
  - verify whether the requester or actor is allowed to see or act on a customer record.
- Capability gate:
  - verify whether the requested action is allowed for the current role, tool, or workflow.

No automated action should trigger unless both gates pass.

### 5. Secure Answering

- Never expose raw sensitive customer data unnecessarily.
- Mask or omit PII in logs and terminal output.
- Require justification for any recommended action affecting a customer.
- Prefer structured outputs over free-form text where possible.

## Recommended Data Choice

Use **synthetic data for the hackathon MVP**.

Why:

- no privacy or compliance risk,
- easy to scale across channels,
- easy to design clear demos,
- easier to create goldens and evals,
- avoids judge questions about consent and access.

Later, if you want more realism, mix synthetic data with public benchmark datasets for behaviors like e-commerce events, support tickets, and churn scenarios.

## CLI Demo Flow

The final command-line demo should look like this:

1. Load interaction data
2. Build unified customer journey
3. Detect friction points
4. Predict likely risk/opportunity
5. Generate next-best action
6. Run ownership gate
7. Run capability gate
8. Return secure decision and explanation
9. Run eval gate summary

## Team Split Suggestion

- Member 1: ingestion + identity resolution
- Member 2: journey builder + friction detection
- Member 3: personalization + next-best action agent
- Member 4: guardrails + evals + demo CLI

## Recommended MVP Story for Judges

“We built an Agentic CX backend that does more than map journeys. It unifies customer events, detects friction, predicts risk, verifies whether actions are allowed, and produces secure next-best actions that can later power a dashboard or workflow engine.”

## Next Build Priority

1. Finalize schemas
2. Generate synthetic dataset
3. Implement CLI pipeline
4. Add guardrails and eval gates
5. Polish the demo narrative

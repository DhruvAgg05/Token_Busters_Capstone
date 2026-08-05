# Implementation Plan

## Build Goal

Deliver a command-line backend MVP that demonstrates end-to-end Agentic CX Intelligence.

## Phase 1: Foundation

Duration:

- Day 1

Deliverables:

- repo scaffold,
- data schemas,
- config files,
- initial CLI entrypoint,
- sample synthetic scenarios.

Tasks:

1. Create repo structure
2. Define unified event schema
3. Define customer profile schema
4. Define journey output schema
5. Define recommendation output schema
6. Define guardrail policy schema

## Phase 2: Data Layer

Duration:

- Day 1 to Day 2

Deliverables:

- synthetic data generator,
- normalized input loaders,
- processed unified customer timeline.

Tasks:

1. Generate customers, events, tickets, transactions, feedback
2. Normalize all records into a shared event model
3. Build identity mapping to a common customer ID
4. Save processed timelines for reuse

## Phase 3: Journey Intelligence

Duration:

- Day 2

Deliverables:

- journey builder,
- stage mapper,
- friction detector.

Tasks:

1. Sort customer events into timeline order
2. Infer journey stage transitions
3. Detect common friction patterns
4. Produce a concise evidence trail

## Phase 4: Personalization + Recommendations

Duration:

- Day 3

Deliverables:

- profile summarizer,
- risk scorer,
- next-best-action engine.

Tasks:

1. Build customer profile from recent and historical behavior
2. Score churn risk / dissatisfaction heuristically
3. Generate recommendation candidates
4. Rank actions using business rules plus prompt logic

## Phase 5: Safety, Verification, and Evals

Duration:

- Day 3 to Day 4

Deliverables:

- ownership gate,
- capability gate,
- secure answer formatter,
- golden-case evaluator,
- eval gate summary.

Tasks:

1. Add role-based ownership checks
2. Add capability checks for allowed actions
3. Mask sensitive fields in output
4. Enforce evidence-backed response schema
5. Create golden eval cases
6. Create pass/fail CLI eval command

## Phase 6: Demo Polish

Duration:

- Day 4

Deliverables:

- demo script,
- sample scenarios,
- judge-friendly explanation flow.

Tasks:

1. Prepare 3 strong customer stories
2. Add terminal-friendly formatting
3. Show why a decision was made
4. Show blocked action example for safety
5. Show eval gate summary after demo run

## Suggested Module Breakdown

### `src/cx_agent/ingestion`

- file loaders
- schema validation
- normalization

### `src/cx_agent/identity`

- customer matching
- customer ID resolution

### `src/cx_agent/journeys`

- timeline builder
- stage inference
- friction detection

### `src/cx_agent/agents`

- predictive experience agent
- next-best-action agent
- journey optimization summarizer

### `src/cx_agent/personalization`

- profile builder
- segmentation
- preference extraction

### `src/cx_agent/guardrails`

- ownership gate
- capability gate
- response policies
- PII masking

### `src/cx_agent/evals`

- golden evaluator
- response scoring
- policy compliance checks

### `src/cx_agent/cli`

- run demo command
- inspect customer journey command
- run eval command

## Recommended CLI Commands

```bash
python scripts/generate_synthetic_data.py
python scripts/run_demo.py --customer CUST_001
python scripts/run_demo.py --scenario onboarding_dropoff
python scripts/run_evals.py
```

## What to Implement as Rules vs LLM

### Use rules first for:

- schema validation,
- stage assignment,
- friction triggers,
- ownership verification,
- capability verification,
- PII masking,
- eval scoring.

### Use LLM for:

- journey summary,
- explanation generation,
- recommendation wording,
- rationale formatting,
- optional retrieval-backed insight synthesis.

This keeps the system credible and easier to defend in front of judges.

## Guardrail Design

### Ownership Gate

Question:

- does this actor have the right to access or act on this customer?

Example:

- support lead can access assigned region,
- sales rep cannot trigger service compensation.

### Capability Gate

Question:

- even if the actor has access, do they have permission to perform the requested action?

Example:

- support analyst can recommend escalation,
- support analyst cannot approve refund.

### Response Policy

Requirements:

- no unsupported claims,
- no unnecessary PII,
- clear confidence or uncertainty,
- evidence-based recommendation,
- blocked response when verification fails.

## Team Execution Plan

### Teammate A

- schemas
- ingestion
- synthetic data generator

### Teammate B

- journey builder
- friction detector

### Teammate C

- personalization
- predictive scoring
- next-best-action logic

### Teammate D

- guardrails
- evals
- CLI demo packaging

## What to Show in the Hackathon Demo

Show two positive flows and one blocked/safe flow.

### Demo 1

- customer at risk due to payment failure and support delay
- system recommends recovery action

### Demo 2

- loyal customer with upsell potential
- system recommends personalized offer

### Demo 3

- requested action fails ownership or capability gate
- system returns secure blocked response

That third demo is important because it proves your system is not just “smart,” but also governed.

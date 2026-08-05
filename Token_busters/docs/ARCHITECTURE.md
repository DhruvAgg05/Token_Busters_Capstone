# Architecture Overview

## System Objective

Create a backend intelligence layer that continuously turns raw customer events into:

- a unified customer journey,
- journey-stage awareness,
- friction alerts,
- predictive risk signals,
- personalized next-best actions,
- secure and explainable decisions.

## High-Level Architecture

```text
Channel Data Sources
    |
    v
Ingestion Layer
    |
    v
Normalization + Identity Resolution
    |
    v
Unified Journey Store
    |
    +--> Friction Detection Agent
    |
    +--> Predictive Experience Agent
    |
    +--> Personalization Engine
    |
    +--> Next Best Action Agent
    |
    +--> Guardrails + Verification Gates
    |
    v
Secure CLI Output / Action Recommendation
```

## Logical Components

### 1. Ingestion Layer

Purpose:

- load CRM, web, app, support, transaction, survey, and communication events.

Responsibilities:

- parse files,
- validate schema,
- normalize timestamps and channel names,
- map source records into a shared event model.

### 2. Identity Resolution

Purpose:

- connect events from multiple channels to one customer profile.

Inputs:

- email hash,
- CRM customer ID,
- device ID,
- ticket ID,
- order ID,
- phone hash.

Output:

- unified `customer_id`.

### 3. Journey Builder

Purpose:

- reconstruct a customer timeline and assign journey stages.

Example stages:

- awareness,
- onboarding,
- purchase,
- support,
- renewal,
- churn-risk,
- retained.

### 4. Friction Detection Agent

Purpose:

- identify pain points and anomalies in the journey.

Example rules:

- repeated support contact within short time,
- payment failure followed by inactivity,
- cart abandonment after coupon failure,
- negative survey after delayed resolution.

### 5. Predictive Experience Agent

Purpose:

- estimate risk or opportunity based on recent events.

Outputs:

- churn risk,
- escalation likelihood,
- upsell suitability,
- service dissatisfaction signal.

For the MVP, this can start with rules plus a simple scored heuristic before moving to ML.

### 6. Personalization Engine

Purpose:

- convert unified profile + recent behavior into useful context for recommendations.

Profile fields:

- preferred channel,
- recent issue category,
- product interest,
- loyalty tier,
- sentiment trend,
- inactivity duration.

### 7. Next Best Action Agent

Purpose:

- recommend the safest, most relevant action.

Examples:

- send onboarding reminder,
- trigger retention offer,
- escalate support priority,
- request callback,
- avoid contacting customer until issue ownership is clarified.

### 8. Guardrails and Verification Gates

Purpose:

- ensure recommendations are authorized, explainable, and safe.

Checks:

- ownership gate,
- capability gate,
- PII masking,
- policy compliance,
- output schema validation,
- evidence-backed explanation.

### 9. Eval Gate

Purpose:

- prevent weak or unsafe demo outputs from being shown as valid.

The CLI should report:

- pass/fail per golden case,
- failed policies,
- uncertain recommendations,
- examples needing manual review.

## Suggested Azure-Aligned Deployment Path

For the hackathon MVP:

- Python CLI app,
- local files for data,
- local vector index optional,
- prompt-driven recommendation layer,
- JSON/CSV outputs.

For the next phase:

- Azure Data Lake for raw and processed data,
- Databricks for pipelines,
- Azure OpenAI for reasoning and summarization,
- Azure SQL or Cosmos DB for indexed journey access,
- Azure AI Search or vector DB for retrieval,
- event-driven orchestration for near-real-time actions.

## Security by Design

### Data Handling

- no raw PII in demo output,
- hash identifiers where possible,
- separate customer facts from display-safe summaries.

### Action Safety

- do not allow autonomous external actions in MVP,
- only recommend actions unless explicitly approved,
- require both gates before any “action allowed” status.

### LLM Safety

- force JSON output schema,
- attach evidence snippets from source events,
- block unsupported claims,
- return “insufficient evidence” when context is weak.

## Recommended Demo Example

Example journey:

1. Customer views premium plan
2. Starts signup
3. Payment fails twice
4. Opens support ticket
5. Receives delayed response
6. Leaves negative survey feedback

Expected engine output:

- journey stage: onboarding-at-risk,
- friction: payment plus support delay,
- predicted risk: churn or drop-off,
- next best action: priority support recovery plus retry guidance,
- ownership gate: passed,
- capability gate: passed for support lead role,
- secure output: masked identifiers and evidence-based explanation.

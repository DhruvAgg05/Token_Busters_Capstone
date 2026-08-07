# Project Pipeline

This project is a customer journey intelligence demo.
It takes fragmented customer signals, combines them into one journey, and shows the business-safe next action.

## End-To-End Flow

```mermaid
flowchart TD
  A["Synthetic customer data"] --> B["Split source files"]
  B --> C["Load customers and events"]
  C --> D["Build customer timeline"]
  D --> E["Analyze journey stage and friction"]
  E --> F["Build customer profile"]
  F --> G["Recommend next best action"]
  G --> H["Check guardrails"]
  H --> I["Mask identity and record audit trail"]
  I --> J["Score with judge rules"]
  J --> K["Optional LLM commentary"]
  K --> L["Show in CLI, API, and UI"]
```

## Step By Step

### 1. Generate synthetic data

- `src/cx_agent/ingestion/synthetic.py` creates the customers, events, and golden scenarios.
- The data is synthetic so the demo is safe to show and easy to explain.
- The theme is SaaS-style customer success and retention, not real customer data.

### 2. Split events by source

- `src/cx_agent/ingestion/files.py` groups events into source buckets like `web`, `app`, `support`, `payments`, `communications`, and `surveys`.
- This is why the demo can say it collects signals from multiple systems.
- The split files live in `data/synthetic/sources/`.

### 3. Merge source feeds into one view

- The pipeline loads the split files and turns them into one unified event stream.
- If needed, it can fall back to the merged `data/synthetic/events.json` file.
- This is the “one customer, many touchpoints” story.

### 4. Build the customer timeline

- `src/cx_agent/journeys/builder.py` sorts all events for one customer by time.
- The result is a clean journey timeline.
- This is what the UI shows as the journey strip.

### 5. Detect the journey problem

- The journey builder looks for patterns like:
  - failed payment attempts
  - form errors
  - dropped onboarding sessions
  - reopened support tickets
  - negative survey feedback
- It then assigns a journey stage such as:
  - `onboarding_at_risk`
  - `onboarding_abandoned`
  - `renewal_at_risk`
  - `service_recovery`
  - `retained_growth`

### 6. Build a customer profile

- `src/cx_agent/personalization/profile.py` turns the timeline into a short profile.
- It captures:
  - preferred channel
  - sentiment
  - recent issue
  - product interest
  - loyalty tier
  - risk level
- This is the personalization layer.

### 7. Recommend the next best action

- `src/cx_agent/agents/recommendations.py` chooses the action that best fits the journey and profile.
- Examples:
  - retention outreach
  - support escalation
  - onboarding recovery
  - upsell
  - nurture
- The recommendation is evidence-based, not random.

### 8. Apply guardrails

- `src/cx_agent/guardrails/verification.py` checks:
  - ownership
  - capability
  - PII masking
- If the actor does not own the region, or the role is not allowed, the action is blocked.
- This is what makes the demo safe and enterprise-friendly.

### 9. Run the LangGraph workflow

- `src/cx_agent/orchestration/graph.py` chains the steps as a LangGraph state machine.
- Each node writes an audit trail entry.
- The graph makes the pipeline feel agentic and traceable.

### 10. Produce the final demo bundle

- `src/cx_agent/orchestration/pipeline.py` combines:
  - the customer story
  - CX analytics
  - judge score
  - presentation summary
- This is the final bundle used by the CLI and UI.

### 11. Score the output

- `src/cx_agent/evals/judge.py` checks whether the result is:
  - evidence-backed
  - privacy-safe
  - governance-explained
  - audit-traced
  - decision-clear
- That score is what the judge sees.

### 12. Optional LLM explanation

- `src/cx_agent/llm/openrouter.py` can create a short explanation or judge commentary if an API key is configured.
- If no key is configured, the demo still works with the rule-based output.

### 13. Present it in three ways

- **CLI** for the technical demo operator.
- **API** for structured access and the dashboard.
- **UI** for the judge-friendly business presentation.

## One-Line Pitch

The pipeline turns scattered customer touchpoints into one governed, explainable customer journey with a safe next action and a judge score.

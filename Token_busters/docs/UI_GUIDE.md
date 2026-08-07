# UI Guide

This is the judge-facing dashboard at `/ui`.
It is designed to show the whole story on one screen.

## What The UI Shows

### 1. Hero Summary

- confirms the API is healthy,
- shows how many scenarios exist,
- shows the current judge score.

### 2. Executive Summary

- explains the demo in plain language,
- shows whether governance allowed or blocked the action,
- shows the customer ID,
- shows the current journey stage,
- shows the unified journey size,
- shows the recommended action,
- shows the judge verdict.

### 3. Control Center

- lets you choose a scenario,
- lets you choose the actor role,
- lets you choose the region,
- lets you toggle optional LLM explanation,
- reruns the presentation bundle on demand.

### 4. Customer Story

- **Journey stage** shows what phase the customer is in.
- **Recommended action** shows the next best action.
- **Judge verdict** shows the score and summary.
- **Journey trace** shows the customer touchpoints in order.
- **Evidence trail** lists why the system reached that conclusion.
- **Gates** show ownership and capability checks.

### 5. CX Analytics

- shows total customers and events,
- shows how many source buckets exist,
- shows source coverage,
- shows journey pattern distribution.

### 6. Audit Trail

- shows what the agent loaded,
- shows what it detected,
- shows what it recommended,
- shows what it verified,
- shows what the judge saw.

## How To Explain It To Judges

Use this simple talk track:

1. “I select a customer scenario.”
2. “The system gathers signals from multiple source files.”
3. “It merges those signals into one journey timeline.”
4. “It detects friction and builds a customer profile.”
5. “It recommends the next best action.”
6. “Guardrails decide whether the action is allowed.”
7. “The audit trail proves why the agent made that decision.”
8. “The judge score tells us whether the output is trustworthy and explainable.”

## What Makes The UI Useful

- It replaces a CLI-only demo with a visual story.
- It makes provenance visible.
- It helps judges see that the system is not guessing from one file.
- It shows that the platform combines analytics, reasoning, governance, and presentation in one place.

## UI Reading Order

When demoing live, read the screen in this order:

1. Executive summary
2. Customer story
3. Journey trace
4. CX analytics
5. Audit trail

That order keeps the explanation short and judge-friendly.

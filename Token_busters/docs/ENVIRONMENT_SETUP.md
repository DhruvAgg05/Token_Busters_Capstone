# Environment Setup

## What to create

Create a local `.env` file in the project root by copying `.env.example`.

## Required for the first MVP

These are the only keys you need immediately for the command-line backend:

### Core

- `APP_ENV`
- `APP_NAME`
- `LOG_LEVEL`
- `MASK_PII`

### OpenRouter

- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL`
- `OPENROUTER_MODEL`
- `OPENROUTER_APP_NAME`
- `OPENROUTER_SITE_URL`
- `OPENROUTER_TIMEOUT_SECONDS`

### Runtime

- `DEFAULT_ACTOR_ROLE`
- `DEFAULT_REGION`
- `DEFAULT_DATA_DIR`
- `DEFAULT_OUTPUT_DIR`
- `ENABLE_LLM`
- `ENABLE_SYNTHETIC_DATA`

### Guardrails

- `PII_SALT`
- `ENABLE_OWNERSHIP_GATE`
- `ENABLE_CAPABILITY_GATE`
- `REQUIRE_EVIDENCE_FOR_RECOMMENDATIONS`

### Eval Gate

- `ENABLE_EVAL_GATE`
- `MIN_EVAL_PASS_RATE`

## Which values are actually important

### Must be filled by you

- `OPENROUTER_API_KEY`
- `PII_SALT`

### Should probably stay as default initially

- `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`
- `OPENROUTER_MODEL=anthropic/claude-sonnet-4`
- `OPENROUTER_APP_NAME=TokenBusters-CX-Agent`
- `OPENROUTER_SITE_URL=http://localhost`
- `OPENROUTER_TIMEOUT_SECONDS=30`
- `MASK_PII=true`
- `ENABLE_OWNERSHIP_GATE=true`
- `ENABLE_CAPABILITY_GATE=true`
- `REQUIRE_EVIDENCE_FOR_RECOMMENDATIONS=true`
- `ENABLE_EVAL_GATE=true`

## Why each important key exists

### `OPENROUTER_API_KEY`

Used to call the LLM through OpenRouter.

### `OPENROUTER_MODEL`

Controls which routed model generates summaries, explanations, and next-best-action wording.

### `PII_SALT`

Used when hashing or masking customer identifiers safely in logs and outputs.

### `ENABLE_OWNERSHIP_GATE`

Prevents the system from approving access or actions when the actor should not own that customer context.

### `ENABLE_CAPABILITY_GATE`

Prevents actions that the actor role is not allowed to perform.

### `REQUIRE_EVIDENCE_FOR_RECOMMENDATIONS`

Forces the engine to justify recommendations from actual journey events instead of unsupported claims.

### `MIN_EVAL_PASS_RATE`

Defines the minimum pass threshold for golden-case checks before the demo is treated as acceptable.

## Not needed right now

You do not need these for the first command-line MVP:

- `VECTOR_DB_*`
- `SQL_DATABASE_URL`
- `AZURE_*`

Those are placeholders for the later production-style version.

## Recommended first `.env`

```env
APP_ENV=local
APP_NAME=cx-agent
LOG_LEVEL=INFO
MASK_PII=true

OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_APP_NAME=TokenBusters-CX-Agent
OPENROUTER_SITE_URL=http://localhost
OPENROUTER_TIMEOUT_SECONDS=30

DEFAULT_ACTOR_ROLE=support_lead
DEFAULT_REGION=IN
DEFAULT_DATA_DIR=data
DEFAULT_OUTPUT_DIR=data/processed
ENABLE_LLM=true
ENABLE_SYNTHETIC_DATA=true

PII_SALT=replace_with_a_long_random_string
ENABLE_OWNERSHIP_GATE=true
ENABLE_CAPABILITY_GATE=true
REQUIRE_EVIDENCE_FOR_RECOMMENDATIONS=true

ENABLE_EVAL_GATE=true
MIN_EVAL_PASS_RATE=0.80
```

## Practical recommendation

For now, arrange these two first:

1. `OPENROUTER_API_KEY`
2. `PII_SALT`

Everything else can start with the defaults in `.env.example`.

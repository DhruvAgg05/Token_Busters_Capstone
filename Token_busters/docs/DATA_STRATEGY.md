# Data Strategy

## Recommendation

Use **synthetic data first** for the hackathon.

This is the strongest choice for a judged prototype because it is:

- safe,
- controllable,
- explainable,
- easy to align with your demo story,
- easy to expand into goldens and eval scenarios.

## Why Not Original Private Data

Using real customer data creates immediate questions:

- Did you have access rights?
- Was customer consent handled?
- How was PII protected?
- Can judges inspect the data safely?

Those questions distract from the technical strength of your idea.

## Best Hybrid Strategy

Build the MVP on synthetic data that mimics realistic customer behavior.

If needed later, mention that the system is designed to integrate with:

- CRM exports,
- web analytics events,
- support tickets,
- survey results,
- transaction logs,
- communication history.

## Synthetic Dataset Design

Create linked datasets across channels.

### 1. Customers

Fields:

- customer_id
- segment
- signup_date
- region
- preferred_channel
- loyalty_tier
- product_family

### 2. Web Events

Fields:

- event_id
- customer_id
- timestamp
- page
- action
- session_id
- device_type

Example actions:

- product_view
- start_signup
- add_to_cart
- checkout_start
- cart_abandon

### 3. App Events

Fields:

- event_id
- customer_id
- timestamp
- screen
- action
- app_version

### 4. Support Tickets

Fields:

- ticket_id
- customer_id
- timestamp_opened
- issue_type
- priority
- resolution_time
- status
- csat_signal

### 5. Transactions

Fields:

- transaction_id
- customer_id
- timestamp
- amount
- product
- payment_status
- renewal_flag

### 6. Surveys / Feedback

Fields:

- survey_id
- customer_id
- timestamp
- channel
- sentiment
- topic
- comment_summary

### 7. Communications

Fields:

- comm_id
- customer_id
- timestamp
- channel
- direction
- template_type
- outcome

## Required Behavioral Patterns

Your synthetic data should intentionally include:

- smooth successful journeys,
- abandoned onboarding,
- repeated complaints,
- payment failures,
- delayed support recovery,
- successful retention cases,
- upsell-ready customers,
- channel-switching behavior,
- negative feedback after product issues.

This matters because the demo is stronger when the system has both positive and negative journeys to analyze.

## Golden Cases

In `data/goldens/`, create 10 to 20 hand-crafted scenarios.

Each scenario should define:

- input events,
- expected journey stage,
- expected friction label,
- expected predicted outcome,
- allowed actions by role,
- blocked actions by role,
- expected secure terminal response.

## Optional Public Datasets for Inspiration

If you want realism without using private enterprise data, you can borrow schema ideas from public datasets such as:

- IBM Telco Customer Churn dataset
- Olist e-commerce dataset
- public helpdesk / support ticket datasets on Kaggle
- public web clickstream samples

Use them for inspiration or schema shaping, not as your only demo source, because they usually do not give you a complete multi-channel journey out of the box.

## Final Recommendation

For this hackathon:

- synthetic data for the main demo,
- small golden dataset for evals,
- optional public dataset references only for realism and vocabulary.

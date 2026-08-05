from __future__ import annotations

from datetime import datetime, timedelta
from random import Random

from cx_agent.models import Customer, Event


def generate_synthetic_dataset(seed: int = 7) -> tuple[list[Customer], list[Event], list[dict[str, str]]]:
    rng = Random(seed)
    base_time = datetime(2026, 8, 1, 9, 0, 0)

    customers = [
        Customer(
            customer_id="CUST_001",
            name="Aarav Mehta",
            region="IN",
            segment="digital_newcomer",
            preferred_channel="email",
            loyalty_tier="silver",
            product_family="premium_plan",
            owner_region="IN",
        ),
        Customer(
            customer_id="CUST_002",
            name="Sara Khan",
            region="IN",
            segment="loyal_growth",
            preferred_channel="app",
            loyalty_tier="gold",
            product_family="family_plan",
            owner_region="IN",
        ),
        Customer(
            customer_id="CUST_003",
            name="James Carter",
            region="US",
            segment="service_recovery",
            preferred_channel="phone",
            loyalty_tier="standard",
            product_family="business_plan",
            owner_region="US",
        ),
        Customer(
            customer_id="CUST_004",
            name="Neha Iyer",
            region="IN",
            segment="onboarding_abandonment",
            preferred_channel="whatsapp",
            loyalty_tier="standard",
            product_family="starter_plan",
            owner_region="IN",
        ),
        Customer(
            customer_id="CUST_005",
            name="Lucas Green",
            region="US",
            segment="renewal_risk",
            preferred_channel="email",
            loyalty_tier="silver",
            product_family="business_plus",
            owner_region="US",
        ),
    ]

    events = [
        Event("EVT_001", "CUST_001", _ts(base_time, 0), "web", "product_view", "awareness", "success", {"product": "premium_plan"}),
        Event("EVT_002", "CUST_001", _ts(base_time, 10), "web", "start_signup", "onboarding", "success", {}),
        Event("EVT_003", "CUST_001", _ts(base_time, 25), "payment", "payment_attempt", "onboarding", "failure", {"attempt": 1}),
        Event("EVT_004", "CUST_001", _ts(base_time, 35), "payment", "payment_attempt", "onboarding", "failure", {"attempt": 2}),
        Event("EVT_005", "CUST_001", _ts(base_time, 60), "support", "ticket_opened", "support", "open", {"issue_type": "payment_failure"}),
        Event("EVT_006", "CUST_001", _ts(base_time, 240), "survey", "survey_submitted", "support", "negative", {"sentiment": "negative"}),
        Event("EVT_007", "CUST_002", _ts(base_time, 5), "web", "product_view", "awareness", "success", {"product": "family_plan_plus"}),
        Event("EVT_008", "CUST_002", _ts(base_time, 20), "app", "feature_used", "usage", "success", {"feature": "family_sharing"}),
        Event("EVT_009", "CUST_002", _ts(base_time, 30), "transaction", "renewal_paid", "renewal", "success", {"amount": 1499}),
        Event("EVT_010", "CUST_002", _ts(base_time, 50), "email", "campaign_click", "engagement", "success", {"offer": "bundle_upgrade"}),
        Event("EVT_011", "CUST_003", _ts(base_time, 8), "app", "login_failure", "usage", "failure", {}),
        Event("EVT_012", "CUST_003", _ts(base_time, 18), "support", "ticket_opened", "support", "open", {"issue_type": "access_issue"}),
        Event("EVT_013", "CUST_003", _ts(base_time, 48), "support", "ticket_reopened", "support", "reopened", {"issue_type": "access_issue"}),
        Event("EVT_014", "CUST_003", _ts(base_time, 72), "survey", "survey_submitted", "support", "negative", {"sentiment": "negative"}),
        Event("EVT_015", "CUST_004", _ts(base_time, 2), "web", "product_view", "awareness", "success", {"product": "starter_plan"}),
        Event("EVT_016", "CUST_004", _ts(base_time, 12), "web", "start_signup", "onboarding", "success", {}),
        Event("EVT_017", "CUST_004", _ts(base_time, 17), "web", "form_error", "onboarding", "failure", {"field": "phone_number"}),
        Event("EVT_018", "CUST_004", _ts(base_time, 28), "web", "session_drop", "onboarding", "abandoned", {"step": "profile_setup"}),
        Event("EVT_019", "CUST_004", _ts(base_time, 1200), "email", "campaign_open", "engagement", "success", {"template": "complete_signup"}),
        Event("EVT_020", "CUST_005", _ts(base_time, 1), "transaction", "renewal_due", "renewal", "pending", {"amount": 2999}),
        Event("EVT_021", "CUST_005", _ts(base_time, 20), "payment", "payment_attempt", "renewal", "failure", {"attempt": 1}),
        Event("EVT_022", "CUST_005", _ts(base_time, 36), "payment", "payment_attempt", "renewal", "failure", {"attempt": 2}),
        Event("EVT_023", "CUST_005", _ts(base_time, 55), "support", "ticket_opened", "support", "open", {"issue_type": "billing_issue"}),
        Event("EVT_024", "CUST_005", _ts(base_time, 1440), "communication", "outbound_message_ignored", "retention", "ignored", {"channel": "email"}),
    ]

    # Small random variation to make the data look less hard-coded while remaining deterministic.
    for event in events:
        event.metadata["score_hint"] = rng.randint(1, 5)

    goldens = [
        {
            "scenario_id": "onboarding_dropoff",
            "customer_id": "CUST_001",
            "expected_stage": "onboarding_at_risk",
            "expected_friction": "payment_failure",
            "expected_category": "service_recovery",
        },
        {
            "scenario_id": "loyal_upsell",
            "customer_id": "CUST_002",
            "expected_stage": "retained_growth",
            "expected_friction": "none",
            "expected_category": "upsell",
        },
        {
            "scenario_id": "ownership_blocked",
            "customer_id": "CUST_003",
            "expected_stage": "service_recovery",
            "expected_friction": "repeated_support_issue",
            "expected_category": "support_escalation",
        },
        {
            "scenario_id": "onboarding_abandonment",
            "customer_id": "CUST_004",
            "expected_stage": "onboarding_abandoned",
            "expected_friction": "form_error",
            "expected_category": "onboarding_recovery",
        },
        {
            "scenario_id": "renewal_risk",
            "customer_id": "CUST_005",
            "expected_stage": "renewal_at_risk",
            "expected_friction": "payment_failure",
            "expected_category": "retention_outreach",
        },
    ]
    return customers, events, goldens


def _ts(base_time: datetime, minutes_after: int) -> str:
    return (base_time + timedelta(minutes=minutes_after)).isoformat()

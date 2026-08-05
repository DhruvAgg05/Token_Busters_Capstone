from __future__ import annotations

from cx_agent.models import Customer, CustomerProfile, Event, JourneyResult


def build_profile(customer: Customer, timeline: list[Event], journey: JourneyResult) -> CustomerProfile:
    recent_issue = "none"
    sentiment = "neutral"
    product_interest = customer.product_family

    for event in reversed(timeline):
        if event.channel == "support" and event.metadata.get("issue_type"):
            recent_issue = str(event.metadata["issue_type"])
            break

    for event in reversed(timeline):
        if event.event_type == "survey_submitted":
            sentiment = str(event.metadata.get("sentiment", event.outcome))
            break

    if any(event.metadata.get("product") for event in timeline):
        product_interest = str(next(event.metadata["product"] for event in timeline if event.metadata.get("product")))

    risk_level = {
        "dropoff_risk": "high",
        "escalation_risk": "high",
        "churn_risk": "high",
        "upsell_ready": "medium",
        "stable": "low",
    }.get(journey.risk_label, "medium")

    return CustomerProfile(
        customer_id=customer.customer_id,
        preferred_channel=customer.preferred_channel,
        sentiment=sentiment,
        recent_issue=recent_issue,
        product_interest=product_interest,
        loyalty_tier=customer.loyalty_tier,
        risk_level=risk_level,
    )

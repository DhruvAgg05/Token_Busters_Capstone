from __future__ import annotations

from cx_agent.models import Customer, Event, JourneyResult


def build_customer_timeline(events: list[Event], customer_id: str) -> list[Event]:
    return sorted(
        [event for event in events if event.customer_id == customer_id],
        key=lambda event: event.timestamp_value(),
    )


def analyze_journey(customer: Customer, timeline: list[Event]) -> JourneyResult:
    event_types = [event.event_type for event in timeline]
    friction_points: list[str] = []
    evidence: list[str] = []
    payment_context = "renewal" if "renewal_due" in event_types else "onboarding"

    if event_types.count("payment_attempt") >= 2 and any(event.outcome == "failure" for event in timeline):
        friction_points.append("payment_failure")
        evidence.append(f"Multiple failed payment attempts detected during {payment_context}.")

    if "form_error" in event_types:
        friction_points.append("form_error")
        evidence.append("The customer encountered a form validation error during signup.")

    if "session_drop" in event_types:
        friction_points.append("session_dropoff")
        evidence.append("The customer dropped out during an onboarding session before completion.")

    if "ticket_reopened" in event_types:
        friction_points.append("repeated_support_issue")
        evidence.append("Support ticket reopened after the initial service interaction.")

    if any(event.event_type == "survey_submitted" and event.outcome == "negative" for event in timeline):
        friction_points.append("negative_feedback")
        evidence.append("Negative customer feedback submitted after recent interactions.")

    if "renewal_paid" in event_types and "campaign_click" in event_types:
        stage = "retained_growth"
        risk_label = "upsell_ready"
    elif "form_error" in friction_points and "session_dropoff" in friction_points:
        stage = "onboarding_abandoned"
        risk_label = "dropoff_risk"
    elif "payment_failure" in friction_points and "renewal_due" in event_types:
        stage = "renewal_at_risk"
        risk_label = "churn_risk"
    elif "payment_failure" in friction_points:
        stage = "onboarding_at_risk"
        risk_label = "dropoff_risk"
    elif "repeated_support_issue" in friction_points:
        stage = "service_recovery"
        risk_label = "escalation_risk"
    else:
        stage = _latest_stage(timeline)
        risk_label = "stable"

    if not friction_points:
        friction_points.append("none")
        evidence.append("No major friction pattern was detected in the current journey window.")

    return JourneyResult(
        customer_id=customer.customer_id,
        journey_stage=stage,
        friction_points=friction_points,
        risk_label=risk_label,
        evidence=evidence,
    )


def _latest_stage(timeline: list[Event]) -> str:
    if not timeline:
        return "unknown"
    return timeline[-1].stage_hint

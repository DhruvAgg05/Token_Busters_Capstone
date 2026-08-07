from __future__ import annotations

from collections.abc import Callable

from cx_agent.models import Customer, Event, JourneyResult


JourneyRule = tuple[Callable[[set[str], list[str]], bool], str, str]


STAGE_RULES: tuple[JourneyRule, ...] = (
    (
        lambda event_types, friction_points: "renewal_paid" in event_types and "campaign_click" in event_types,
        "retained_growth",
        "upsell_ready",
    ),
    (
        lambda event_types, friction_points: {"form_error", "session_dropoff"}.issubset(friction_points),
        "onboarding_abandoned",
        "dropoff_risk",
    ),
    (
        lambda event_types, friction_points: "payment_failure" in friction_points and "renewal_due" in event_types,
        "renewal_at_risk",
        "churn_risk",
    ),
    (
        lambda event_types, friction_points: "payment_failure" in friction_points,
        "onboarding_at_risk",
        "dropoff_risk",
    ),
    (
        lambda event_types, friction_points: "repeated_support_issue" in friction_points,
        "service_recovery",
        "escalation_risk",
    ),
)


def build_customer_timeline(events: list[Event], customer_id: str) -> list[Event]:
    return sorted(
        [event for event in events if event.customer_id == customer_id],
        key=lambda event: event.timestamp_value(),
    )


def analyze_journey(customer: Customer, timeline: list[Event]) -> JourneyResult:
    event_types = [event.event_type for event in timeline]
    event_type_set = set(event_types)
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

    stage, risk_label = _match_stage(event_type_set, friction_points, timeline)

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


def _match_stage(event_types: set[str], friction_points: list[str], timeline: list[Event]) -> tuple[str, str]:
    return next(
        (
            (stage, risk_label)
            for predicate, stage, risk_label in STAGE_RULES
            if predicate(event_types, friction_points)
        ),
        (_latest_stage(timeline), "stable"),
    )

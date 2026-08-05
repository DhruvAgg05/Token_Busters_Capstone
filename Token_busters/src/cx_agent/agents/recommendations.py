from __future__ import annotations

from cx_agent.models import Customer, CustomerProfile, JourneyResult, RecommendationResult


def recommend_next_best_action(
    customer: Customer,
    profile: CustomerProfile,
    journey: JourneyResult,
    require_evidence: bool,
) -> RecommendationResult:
    if "payment_failure" in journey.friction_points:
        if journey.journey_stage == "renewal_at_risk":
            return RecommendationResult(
                customer_id=customer.customer_id,
                recommended_action="Trigger a retention outreach with billing assistance and a renewal recovery callback.",
                recommendation_category="retention_outreach",
                rationale="The customer has repeated renewal payment failures and has already opened a billing-related support issue.",
                requires_manual_review=False,
            )
        return RecommendationResult(
            customer_id=customer.customer_id,
            recommended_action="Offer payment recovery guidance and prioritize support follow-up.",
            recommendation_category="service_recovery",
            rationale="The customer hit repeated payment failures and then opened support, which suggests onboarding friction.",
            requires_manual_review=False,
        )

    if "form_error" in journey.friction_points and "session_dropoff" in journey.friction_points:
        return RecommendationResult(
            customer_id=customer.customer_id,
            recommended_action="Send a guided signup recovery message with a simplified onboarding path.",
            recommendation_category="onboarding_recovery",
            rationale="The customer encountered a form error and abandoned the signup flow before completion.",
            requires_manual_review=False,
        )

    if journey.risk_label == "upsell_ready":
        return RecommendationResult(
            customer_id=customer.customer_id,
            recommended_action="Send a personalized premium bundle offer in the customer's preferred channel.",
            recommendation_category="upsell",
            rationale="The customer renewed successfully, engaged with an offer, and shows healthy usage behavior.",
            requires_manual_review=False,
        )

    if "repeated_support_issue" in journey.friction_points:
        return RecommendationResult(
            customer_id=customer.customer_id,
            recommended_action="Escalate to a senior support queue and avoid automated promotional outreach.",
            recommendation_category="support_escalation",
            rationale="The customer reopened a support issue and later submitted negative feedback.",
            requires_manual_review=False,
        )

    fallback_rationale = "Evidence-backed recommendation is not strong enough yet." if require_evidence else "General engagement follow-up is acceptable."
    return RecommendationResult(
        customer_id=customer.customer_id,
        recommended_action="Monitor the account and send a low-risk engagement message.",
        recommendation_category="nurture",
        rationale=fallback_rationale,
        requires_manual_review=require_evidence,
    )

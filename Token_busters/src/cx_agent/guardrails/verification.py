from __future__ import annotations

from hashlib import sha256

from cx_agent.models import Customer, GateResult, RecommendationResult


ROLE_CAPABILITIES = {
    "support_lead": {"service_recovery", "support_escalation", "onboarding_recovery", "nurture"},
    "sales_manager": {"upsell", "retention_outreach", "nurture"},
    "customer_success_manager": {"service_recovery", "onboarding_recovery", "retention_outreach", "nurture"},
    "compliance_viewer": set(),
}


def ownership_gate(customer: Customer, actor_region: str, enabled: bool) -> GateResult:
    if not enabled:
        return GateResult("ownership", True, "Ownership gate disabled in configuration.")
    if customer.owner_region == actor_region:
        return GateResult("ownership", True, "Actor region matches the customer ownership region.")
    return GateResult("ownership", False, "Actor does not own the customer's operational region.")


def capability_gate(actor_role: str, recommendation: RecommendationResult, enabled: bool) -> GateResult:
    if not enabled:
        return GateResult("capability", True, "Capability gate disabled in configuration.")
    allowed = ROLE_CAPABILITIES.get(actor_role, set())
    if recommendation.recommendation_category in allowed:
        return GateResult("capability", True, "Actor role can perform the recommended action category.")
    return GateResult("capability", False, "Actor role is not allowed to perform the recommended action category.")


def mask_customer_id(customer_id: str, salt: str, enabled: bool) -> str:
    if not enabled:
        return customer_id
    digest = sha256(f"{salt}:{customer_id}".encode("utf-8")).hexdigest()
    return f"CUST_MASKED_{digest[:8]}"

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app_name: str
    llm_enabled: bool
    eval_gate_enabled: bool


class ScenarioRecord(BaseModel):
    scenario_id: str
    customer_id: str
    expected_stage: str
    expected_friction: str
    expected_category: str


class ScenarioListResponse(BaseModel):
    scenarios: list[ScenarioRecord]


class AnalyticsResponse(BaseModel):
    totals: dict[str, int]
    source_counts: dict[str, int]
    channel_counts: dict[str, int]
    stage_counts: dict[str, int]
    risk_counts: dict[str, int]
    friction_counts: dict[str, int]


class EventResponse(BaseModel):
    event_id: str
    customer_id: str
    timestamp: str
    channel: str
    event_type: str
    stage_hint: str
    outcome: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class JourneyResponse(BaseModel):
    customer_id: str
    journey_stage: str
    friction_points: list[str]
    risk_label: str
    evidence: list[str]


class ProfileResponse(BaseModel):
    customer_id: str
    preferred_channel: str
    sentiment: str
    recent_issue: str
    product_interest: str
    loyalty_tier: str
    risk_level: str


class RecommendationResponse(BaseModel):
    customer_id: str
    recommended_action: str
    recommendation_category: str
    rationale: str
    requires_manual_review: bool


class GateResponse(BaseModel):
    gate_name: str
    passed: bool
    reason: str


class AuditEntryResponse(BaseModel):
    step: str
    message: str
    timestamp: str
    details: dict[str, Any] = Field(default_factory=dict)


class JudgeResponse(BaseModel):
    enabled: bool
    used: bool
    score: int
    passed: bool
    summary: str
    criteria: dict[str, bool]
    error: str | None = None


class LLMExplanationResponse(BaseModel):
    enabled: bool
    used: bool
    summary: str
    error: str | None = None


class CustomerFactsResponse(BaseModel):
    enabled: bool
    used: bool
    summary: str
    problem_statement: str
    facts: list[str]
    source_signals: list[str]
    error: str | None = None


class UnifiedJourneyResponse(BaseModel):
    enabled: bool
    used: bool
    summary: str
    key_touchpoints: list[str]
    source_signals: list[str]
    error: str | None = None


class DemoResponse(BaseModel):
    customer_id: str
    actor_role: str
    actor_region: str
    governance_status: str
    blocked_reasons: list[str]
    safe_next_step: str
    decision_summary: str
    timeline: list[EventResponse]
    journey: JourneyResponse
    profile: ProfileResponse
    recommendation: RecommendationResponse
    gates: list[GateResponse]
    action_allowed: bool
    audit_trail: list[AuditEntryResponse]
    judge: JudgeResponse | None = None
    llm_explanation: LLMExplanationResponse | None = None
    customer_facts: CustomerFactsResponse | None = None
    unified_journey: UnifiedJourneyResponse | None = None


class JudgeReviewResponse(BaseModel):
    customer_id: str
    actor_role: str
    actor_region: str
    governance_status: str
    decision_summary: str
    judge: JudgeResponse
    safe_next_step: str


class PresentationResponse(BaseModel):
    presentation_summary: str
    demo: DemoResponse
    analytics: AnalyticsResponse
    judge: JudgeResponse | None = None


class TimelineResponse(BaseModel):
    customer_id: str
    scenario_id: str | None = None
    actor_role: str
    actor_region: str
    journey_stage: str
    timeline: list[EventResponse]


class EvalCaseResponse(BaseModel):
    scenario_id: str
    customer_id: str
    scores: dict[str, bool]


class EvalSummaryResponse(BaseModel):
    total_cases: float
    total_checks: float
    passed_checks: float
    pass_rate: float
    passed_gate: bool


class EvalResponse(BaseModel):
    summary: EvalSummaryResponse
    details: list[EvalCaseResponse]

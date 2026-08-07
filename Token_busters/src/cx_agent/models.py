from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Customer:
    customer_id: str
    name: str
    region: str
    segment: str
    preferred_channel: str
    loyalty_tier: str
    product_family: str
    owner_region: str


@dataclass
class Event:
    event_id: str
    customer_id: str
    timestamp: str
    channel: str
    event_type: str
    stage_hint: str
    outcome: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def timestamp_value(self) -> datetime:
        return datetime.fromisoformat(self.timestamp)


@dataclass
class CustomerProfile:
    customer_id: str
    preferred_channel: str
    sentiment: str
    recent_issue: str
    product_interest: str
    loyalty_tier: str
    risk_level: str


@dataclass
class JourneyResult:
    customer_id: str
    journey_stage: str
    friction_points: list[str]
    risk_label: str
    evidence: list[str]


@dataclass
class RecommendationResult:
    customer_id: str
    recommended_action: str
    recommendation_category: str
    rationale: str
    requires_manual_review: bool


@dataclass
class GateResult:
    gate_name: str
    passed: bool
    reason: str


@dataclass
class AuditEntry:
    step: str
    message: str
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class JudgeResult:
    enabled: bool
    used: bool
    score: int
    passed: bool
    summary: str
    criteria: dict[str, bool]
    error: str | None = None


def to_dict(model: Any) -> dict[str, Any]:
    return asdict(model)

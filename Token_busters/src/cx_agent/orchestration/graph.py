from __future__ import annotations

from datetime import datetime, timezone
from collections import Counter
from operator import add
from typing import Annotated, TypedDict
from functools import lru_cache

from langgraph.graph import END, StateGraph

from cx_agent.guardrails.verification import capability_gate, mask_customer_id, ownership_gate
from cx_agent.ingestion.files import source_bucket_for_channel
from cx_agent.journeys.builder import analyze_journey, build_customer_timeline
from cx_agent.llm.openrouter import generate_customer_profile, generate_explanation, generate_recommendation
from cx_agent.models import AuditEntry, Customer, Event
from cx_agent.settings import Settings


class DemoGraphState(TypedDict, total=False):
    settings: Settings
    customer: Customer
    events: list[Event]
    actor_role: str
    actor_region: str
    include_llm: bool
    timeline: list[Event]
    journey: object
    profile: object
    recommendation: object
    gates: list[object]
    action_allowed: bool
    masked_customer_id: str
    llm_explanation: object
    audit_trail: Annotated[list[AuditEntry], add]


def run_demo_graph(
    settings: Settings,
    customer: Customer,
    events: list[Event],
    actor_role: str,
    actor_region: str,
    include_llm: bool,
) -> DemoGraphState:
    graph = _build_graph()
    return graph.invoke(
        {
            "settings": settings,
            "customer": customer,
            "events": events,
            "actor_role": actor_role,
            "actor_region": actor_region,
            "include_llm": include_llm,
            "audit_trail": [],
        }
    )


@lru_cache(maxsize=1)
def _build_graph() -> StateGraph:
    graph = StateGraph(DemoGraphState)
    graph.add_node("build_timeline", _build_timeline_node)
    graph.add_node("analyze_journey", _analyze_journey_node)
    graph.add_node("build_profile", _build_profile_node)
    graph.add_node("recommend", _recommend_node)
    graph.add_node("verify", _verify_node)
    graph.add_node("llm_explain", _llm_explain_node)

    graph.set_entry_point("build_timeline")
    graph.add_edge("build_timeline", "analyze_journey")
    graph.add_edge("analyze_journey", "build_profile")
    graph.add_edge("build_profile", "recommend")
    graph.add_edge("recommend", "verify")
    graph.add_conditional_edges("verify", _route_after_verify, {"llm_explain": "llm_explain", "end": END})
    graph.add_edge("llm_explain", END)
    return graph.compile()


def _build_timeline_node(state: DemoGraphState) -> dict[str, object]:
    customer = state["customer"]
    timeline = build_customer_timeline(state["events"], customer.customer_id)
    source_counts = Counter(source_bucket_for_channel(event.channel) for event in timeline)
    first_event = timeline[0].timestamp if timeline else "n/a"
    last_event = timeline[-1].timestamp if timeline else "n/a"
    return {
        "timeline": timeline,
        "audit_trail": [
            _audit(
                "build_timeline",
                f"Loaded {len(timeline)} events across {len(source_counts)} source buckets.",
                {
                    "source_counts": dict(sorted(source_counts.items())),
                    "first_event": first_event,
                    "last_event": last_event,
                },
            )
        ],
    }


def _analyze_journey_node(state: DemoGraphState) -> dict[str, object]:
    customer = state["customer"]
    journey = analyze_journey(customer, state["timeline"])
    return {
        "journey": journey,
        "audit_trail": [
            _audit(
                "analyze_journey",
                f"Detected stage {journey.journey_stage} with friction {'/'.join(journey.friction_points)}.",
                {
                    "journey_stage": journey.journey_stage,
                    "risk_label": journey.risk_label,
                    "friction_points": journey.friction_points,
                },
            )
        ],
    }


def _build_profile_node(state: DemoGraphState) -> dict[str, object]:
    customer = state["customer"]
    profile, used, error = generate_customer_profile(
        state["settings"],
        customer,
        state["timeline"],  # type: ignore[arg-type]
        state["journey"],  # type: ignore[arg-type]
    )
    return {
        "profile": profile,
        "audit_trail": [
            _audit(
                "build_profile",
                f"Built profile with channel {profile.preferred_channel} and risk {profile.risk_level}.",
                {
                    "preferred_channel": profile.preferred_channel,
                    "sentiment": profile.sentiment,
                    "recent_issue": profile.recent_issue,
                    "risk_level": profile.risk_level,
                    "used_llm": used,
                    "llm_error": error,
                },
            )
        ],
    }


def _recommend_node(state: DemoGraphState) -> dict[str, object]:
    customer = state["customer"]
    recommendation, used, error = generate_recommendation(
        state["settings"],
        customer,
        state["profile"],  # type: ignore[arg-type]
        state["journey"],  # type: ignore[arg-type]
    )
    return {
        "recommendation": recommendation,
        "audit_trail": [
            _audit(
                "recommend",
                f"Recommended category {recommendation.recommendation_category}.",
                {
                    "recommendation_category": recommendation.recommendation_category,
                    "requires_manual_review": recommendation.requires_manual_review,
                    "used_llm": used,
                    "llm_error": error,
                },
            )
        ],
    }


def _verify_node(state: DemoGraphState) -> dict[str, object]:
    customer = state["customer"]
    settings = state["settings"]
    actor_role = state["actor_role"]
    actor_region = state["actor_region"]
    recommendation = state["recommendation"]  # type: ignore[assignment]
    own_gate = ownership_gate(customer, actor_region, settings.enable_ownership_gate)
    cap_gate = capability_gate(actor_role, recommendation, settings.enable_capability_gate)
    masked_customer_id = mask_customer_id(customer.customer_id, settings.pii_salt, settings.mask_pii)
    action_allowed = own_gate.passed and cap_gate.passed
    return {
        "gates": [own_gate, cap_gate],
        "action_allowed": action_allowed,
        "masked_customer_id": masked_customer_id,
        "audit_trail": [
            _audit(
                "verify",
                f"Ownership {'passed' if own_gate.passed else 'blocked'} and capability {'passed' if cap_gate.passed else 'blocked'}.",
                {
                    "ownership": {
                        "passed": own_gate.passed,
                        "reason": own_gate.reason,
                    },
                    "capability": {
                        "passed": cap_gate.passed,
                        "reason": cap_gate.reason,
                    },
                    "action_allowed": action_allowed,
                },
            )
        ],
    }


def _llm_explain_node(state: DemoGraphState) -> dict[str, object]:
    explanation = generate_explanation(
        state["settings"],
        state["masked_customer_id"],
        state["journey"],  # type: ignore[arg-type]
        state["recommendation"],  # type: ignore[arg-type]
        state["gates"],  # type: ignore[arg-type]
        state["action_allowed"],
    )
    return {
        "llm_explanation": explanation,
        "audit_trail": [_audit("llm_explain", "Generated optional LLM explanation.", {"used": explanation.used, "enabled": explanation.enabled})],
    }


def _route_after_verify(state: DemoGraphState) -> str:
    return "llm_explain" if state.get("include_llm") else "end"


def _audit(step: str, message: str, details: dict[str, object] | None = None) -> AuditEntry:
    return AuditEntry(
        step=step,
        message=message,
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={} if details is None else details,
    )

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
from uuid import uuid4

from cx_agent.evals.judge import judge_demo_output
from cx_agent.evals.golden import evaluate_case, summarize_scores
from cx_agent.ingestion.files import (
    load_customers,
    load_events,
    load_events_from_source_directory,
    read_json,
    source_bucket_for_channel,
)
from cx_agent.models import to_dict
from cx_agent.journeys.builder import analyze_journey, build_customer_timeline
from cx_agent.orchestration.graph import run_demo_graph
from cx_agent.settings import Settings


def load_demo_data(data_root: Path) -> tuple[list, list, list[dict[str, str]]]:
    synthetic_root = data_root / "synthetic"
    customers = load_customers(synthetic_root / "customers.json")
    source_directory = synthetic_root / "sources"
    events = load_events_from_source_directory(source_directory)
    if not events:
        events = load_events(synthetic_root / "events.json")
    goldens = read_json(synthetic_root / "goldens.json")
    return customers, events, goldens


def find_customer_id_by_scenario(data_root: Path, scenario_id: str) -> str:
    _, _, goldens = load_demo_data(data_root)
    try:
        return next(golden["customer_id"] for golden in goldens if golden["scenario_id"] == scenario_id)
    except StopIteration as exc:
        raise ValueError(f"Unknown scenario_id: {scenario_id}") from exc


def run_customer_demo(
    settings: Settings,
    customer_id: str,
    actor_role: str | None = None,
    actor_region: str | None = None,
    include_llm: bool = False,
) -> dict[str, object]:
    customers, events, _ = load_demo_data(settings.default_data_dir)
    try:
        customer = next(customer for customer in customers if customer.customer_id == customer_id)
    except StopIteration as exc:
        raise ValueError(f"Unknown customer_id: {customer_id}") from exc

    role = actor_role or settings.default_actor_role
    region = actor_region or settings.default_region
    graph_state = run_demo_graph(settings, customer, events, role, region, include_llm)
    raw_result = {
        "customer_id": graph_state["masked_customer_id"],
        "actor_role": role,
        "actor_region": region,
        "timeline": graph_state["timeline"],
        "journey": graph_state["journey"],
        "profile": graph_state["profile"],
        "recommendation": graph_state["recommendation"],
        "gates": graph_state["gates"],
        "action_allowed": graph_state["action_allowed"],
        "llm_explanation": graph_state.get("llm_explanation"),
        "audit_trail": graph_state["audit_trail"],
    }
    serialized_result = serialize_demo_result(raw_result)
    judge_result = judge_demo_output(settings, serialized_result)
    demo_result = {**raw_result, "judge": judge_result}
    persisted_payload = serialize_demo_result(demo_result)

    _persist_run_artifact(
        settings,
        artifact_type="customer_demo",
        payload=persisted_payload,
    )
    return demo_result


def run_judge_review(
    settings: Settings,
    customer_id: str,
    actor_role: str | None = None,
    actor_region: str | None = None,
    include_llm: bool = False,
) -> dict[str, object]:
    demo_result = run_customer_demo(settings, customer_id, actor_role, actor_region, include_llm)
    serialized = serialize_demo_result(demo_result)
    return {
        "customer_id": serialized["customer_id"],
        "actor_role": serialized["actor_role"],
        "actor_region": serialized["actor_region"],
        "governance_status": "allowed" if serialized["action_allowed"] else "blocked",
        "decision_summary": _build_decision_summary(serialized),
        "safe_next_step": _safe_next_step(serialized),
        "judge": serialized["judge"],
    }


def run_presentation(
    settings: Settings,
    customer_id: str,
    actor_role: str | None = None,
    actor_region: str | None = None,
    include_llm: bool = False,
) -> dict[str, object]:
    demo_result = run_customer_demo(settings, customer_id, actor_role, actor_region, include_llm)
    serialized_demo = serialize_demo_result(demo_result)
    analytics = run_cx_analytics(settings)
    decorated_demo = decorate_demo_payload(serialized_demo)
    judge = serialized_demo["judge"]
    return {
        "demo": decorated_demo,
        "analytics": analytics,
        "judge": judge,
        "presentation_summary": _build_presentation_summary(decorated_demo, analytics, judge),
    }


def run_eval_suite(settings: Settings) -> dict[str, object]:
    customers, events, goldens = load_demo_data(settings.default_data_dir)
    customer_map = {customer.customer_id: customer for customer in customers}
    score_rows: list[dict[str, bool]] = []
    detailed_rows: list[dict[str, object]] = []

    for golden in goldens:
        customer = customer_map[golden["customer_id"]]
        graph_state = run_demo_graph(
            settings,
            customer,
            events,
            settings.default_actor_role,
            settings.default_region,
            include_llm=False,
        )
        case_scores = evaluate_case(
            golden["expected_stage"],
            golden["expected_friction"],
            golden["expected_category"],
            graph_state["journey"],
            graph_state["recommendation"],
        )
        score_rows.append(case_scores)
        detailed_rows.append(
            {
                "scenario_id": golden["scenario_id"],
                "customer_id": golden["customer_id"],
                "scores": case_scores,
            }
        )

    summary = summarize_scores(score_rows)
    summary["passed_gate"] = summary["pass_rate"] >= settings.min_eval_pass_rate
    return {"summary": summary, "details": detailed_rows}


def run_cx_analytics(settings: Settings) -> dict[str, object]:
    customers, events, goldens = load_demo_data(settings.default_data_dir)
    source_counts = Counter(source_bucket_for_channel(event.channel) for event in events)
    channel_counts = Counter(event.channel for event in events)
    stage_counts: Counter[str] = Counter()
    friction_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()

    for customer in customers:
        timeline = build_customer_timeline(events, customer.customer_id)
        journey = analyze_journey(customer, timeline)
        stage_counts[journey.journey_stage] += 1
        risk_counts[journey.risk_label] += 1
        for friction in journey.friction_points:
            friction_counts[friction] += 1

    return {
        "totals": {
            "customers": len(customers),
            "events": len(events),
            "golden_scenarios": len(goldens),
            "source_buckets": len(source_counts),
            "channels": len(channel_counts),
        },
        "source_counts": dict(sorted(source_counts.items())),
        "channel_counts": dict(sorted(channel_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "risk_counts": dict(sorted(risk_counts.items())),
        "friction_counts": dict(sorted(friction_counts.items())),
    }


def serialize_demo_result(result: dict[str, object]) -> dict[str, object]:
    masked_customer_id = result["customer_id"]
    timeline = [_mask_customer_fields(to_dict(event), masked_customer_id) for event in result["timeline"]]
    gates = [to_dict(gate) for gate in result["gates"]]
    llm_explanation = result["llm_explanation"]
    audit_trail = result.get("audit_trail", [])
    judge = result.get("judge")
    journey = _mask_customer_fields(to_dict(result["journey"]), masked_customer_id)
    profile = _mask_customer_fields(to_dict(result["profile"]), masked_customer_id)
    recommendation = _mask_customer_fields(to_dict(result["recommendation"]), masked_customer_id)

    return {
        "customer_id": masked_customer_id,
        "actor_role": result["actor_role"],
        "actor_region": result["actor_region"],
        "timeline": timeline,
        "journey": journey,
        "profile": profile,
        "recommendation": recommendation,
        "gates": gates,
        "action_allowed": result["action_allowed"],
        "llm_explanation": None if llm_explanation is None else to_dict(llm_explanation),
        "audit_trail": [to_dict(item) for item in audit_trail],
        "judge": None if judge is None else to_dict(judge),
    }


def _build_decision_summary(serialized: dict[str, object]) -> str:
    journey = serialized["journey"]
    recommendation = serialized["recommendation"]
    governance_status = "allowed" if serialized["action_allowed"] else "blocked"
    if governance_status == "allowed":
        return (
            f"Customer {serialized['customer_id']} is in stage {journey['journey_stage']} with "
            f"risk {journey['risk_label']}. The recommended action is "
            f"{recommendation['recommendation_category']} and it passed governance checks."
        )
    return (
        f"Customer {serialized['customer_id']} is in stage {journey['journey_stage']} with "
        f"risk {journey['risk_label']}. The recommended action is "
        f"{recommendation['recommendation_category']}, but it is blocked by governance checks."
    )


def _safe_next_step(serialized: dict[str, object]) -> str:
    gates = serialized["gates"]
    blocked_gate_names = [gate["gate_name"] for gate in gates if not gate["passed"]]
    if not blocked_gate_names:
        return "The action passed governance checks and can proceed through an approved workflow."
    if "ownership" in blocked_gate_names and "capability" in blocked_gate_names:
        return "Use an authorized actor with both the correct ownership scope and the required action capability."
    if "ownership" in blocked_gate_names:
        return "Route this case to an actor who owns the customer's region or account scope."
    return "Route this action to a role that is allowed to perform the recommended intervention."


def decorate_demo_payload(serialized: dict[str, object]) -> dict[str, object]:
    gates = serialized["gates"]
    blocked_reasons = [gate["reason"] for gate in gates if not gate["passed"]]
    action_allowed = bool(serialized["action_allowed"])
    governance_status = "allowed" if action_allowed else "blocked"
    safe_next_step = _safe_next_step(serialized)
    decision_summary = _build_decision_summary(serialized)
    enriched = dict(serialized)
    enriched["governance_status"] = governance_status
    enriched["blocked_reasons"] = blocked_reasons
    enriched["safe_next_step"] = safe_next_step
    enriched["decision_summary"] = decision_summary
    return enriched


def _build_presentation_summary(
    serialized_demo: dict[str, object],
    analytics: dict[str, object],
    judge: dict[str, object] | None,
) -> str:
    journey = serialized_demo["journey"]
    totals = analytics["totals"]
    judge_score = "n/a" if judge is None else f"{judge['score']}/100"
    return (
        f"Customer {serialized_demo['customer_id']} is in stage {journey['journey_stage']} "
        f"while the dataset contains {totals['customers']} customers and {totals['events']} events. "
        f"Judge score: {judge_score}."
    )


def _mask_customer_fields(payload: dict[str, object], masked_customer_id: str) -> dict[str, object]:
    output = dict(payload)
    if "customer_id" in output:
        output["customer_id"] = masked_customer_id
    return output


def _persist_run_artifact(settings: Settings, artifact_type: str, payload: dict[str, object]) -> None:
    run_directory = settings.default_output_dir / "audit_runs"
    run_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    customer_id = str(payload.get("customer_id", "unknown"))
    safe_customer_id = customer_id.replace("/", "_").replace("\\", "_")
    file_name = f"{timestamp}_{artifact_type}_{safe_customer_id}_{uuid4().hex[:8]}.json"
    artifact = {
        "artifact_type": artifact_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    (run_directory / file_name).write_text(json.dumps(artifact, indent=2), encoding="utf-8")

from __future__ import annotations

from pathlib import Path

from cx_agent.agents.recommendations import recommend_next_best_action
from cx_agent.evals.golden import evaluate_case, summarize_scores
from cx_agent.guardrails.verification import capability_gate, mask_customer_id, ownership_gate
from cx_agent.ingestion.files import load_customers, load_events, read_json
from cx_agent.models import to_dict
from cx_agent.journeys.builder import analyze_journey, build_customer_timeline
from cx_agent.llm.openrouter import generate_explanation
from cx_agent.personalization.profile import build_profile
from cx_agent.settings import Settings


def load_demo_data(data_root: Path) -> tuple[list, list, list[dict[str, str]]]:
    synthetic_root = data_root / "synthetic"
    customers = load_customers(synthetic_root / "customers.json")
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
    timeline = build_customer_timeline(events, customer_id)
    journey = analyze_journey(customer, timeline)
    profile = build_profile(customer, timeline, journey)
    recommendation = recommend_next_best_action(
        customer,
        profile,
        journey,
        settings.require_evidence_for_recommendations,
    )

    role = actor_role or settings.default_actor_role
    region = actor_region or settings.default_region
    own_gate = ownership_gate(customer, region, settings.enable_ownership_gate)
    cap_gate = capability_gate(role, recommendation, settings.enable_capability_gate)
    masked_customer_id = mask_customer_id(customer.customer_id, settings.pii_salt, settings.mask_pii)
    action_allowed = own_gate.passed and cap_gate.passed
    llm_explanation = generate_explanation(
        settings,
        masked_customer_id,
        journey,
        recommendation,
        [own_gate, cap_gate],
        action_allowed,
    ) if include_llm else None

    return {
        "customer_id": masked_customer_id,
        "actor_role": role,
        "actor_region": region,
        "timeline": timeline,
        "journey": journey,
        "profile": profile,
        "recommendation": recommendation,
        "gates": [own_gate, cap_gate],
        "action_allowed": action_allowed,
        "llm_explanation": llm_explanation,
    }


def run_eval_suite(settings: Settings) -> dict[str, object]:
    customers, events, goldens = load_demo_data(settings.default_data_dir)
    customer_map = {customer.customer_id: customer for customer in customers}
    score_rows: list[dict[str, bool]] = []
    detailed_rows: list[dict[str, object]] = []

    for golden in goldens:
        customer = customer_map[golden["customer_id"]]
        timeline = build_customer_timeline(events, golden["customer_id"])
        journey = analyze_journey(customer, timeline)
        profile = build_profile(customer, timeline, journey)
        recommendation = recommend_next_best_action(
            customer,
            profile,
            journey,
            settings.require_evidence_for_recommendations,
        )
        case_scores = evaluate_case(
            golden["expected_stage"],
            golden["expected_friction"],
            golden["expected_category"],
            journey,
            recommendation,
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


def serialize_demo_result(result: dict[str, object]) -> dict[str, object]:
    masked_customer_id = result["customer_id"]
    timeline = [_mask_customer_fields(to_dict(event), masked_customer_id) for event in result["timeline"]]
    gates = [to_dict(gate) for gate in result["gates"]]
    llm_explanation = result["llm_explanation"]
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
    }


def _mask_customer_fields(payload: dict[str, object], masked_customer_id: str) -> dict[str, object]:
    output = dict(payload)
    if "customer_id" in output:
        output["customer_id"] = masked_customer_id
    return output

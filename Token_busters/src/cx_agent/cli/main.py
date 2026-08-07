from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cx_agent.models import Event, GateResult, JourneyResult, RecommendationResult
from cx_agent.orchestration.pipeline import (
    find_customer_id_by_scenario,
    load_demo_data,
    run_cx_analytics,
    run_customer_demo,
    run_eval_suite,
    run_judge_review,
    run_presentation,
    serialize_demo_result,
)
from cx_agent.settings import load_settings


def _console_safe(text: object) -> str:
    return str(text).encode("ascii", errors="replace").decode("ascii")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    settings = load_settings()
    parser = argparse.ArgumentParser(description="Agentic CX command-line demo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate-data", help="Generate synthetic demo data")
    generate_parser.add_argument("--seed", type=int, default=7, help="Seed for deterministic synthetic data.")

    list_parser = subparsers.add_parser("list-scenarios", help="List available golden demo scenarios")
    list_parser.add_argument("--verbose", action="store_true", help="Show expected stage and category")

    demo_parser = subparsers.add_parser("demo", help="Run a customer or scenario demo")
    demo_parser.add_argument("--customer", help="Customer ID to inspect.")
    demo_parser.add_argument("--scenario", help="Scenario ID from the golden dataset.")
    demo_parser.add_argument("--role", help="Actor role override.")
    demo_parser.add_argument("--region", help="Actor region override.")
    demo_parser.add_argument("--with-llm", action="store_true", help="Include an OpenRouter-generated explanation.")
    demo_parser.add_argument("--show-timeline", action="store_true", help="Print the customer event timeline.")
    demo_parser.add_argument("--output-json", help="Write the demo result to a JSON file.")

    eval_parser = subparsers.add_parser("evals", help="Run golden evals")
    eval_parser.add_argument("--show-details", action="store_true", help="Print per-scenario eval results.")

    analytics_parser = subparsers.add_parser("analytics", help="Show CX summary analytics")
    analytics_parser.add_argument("--show-details", action="store_true", help="Print source and journey breakdowns")

    judge_parser = subparsers.add_parser("judge", help="Run the judge score only")
    judge_parser.add_argument("--customer", help="Customer ID to inspect.")
    judge_parser.add_argument("--scenario", help="Scenario ID from the golden dataset.")
    judge_parser.add_argument("--role", help="Actor role override.")
    judge_parser.add_argument("--region", help="Actor region override.")
    judge_parser.add_argument("--with-llm", action="store_true", help="Include an OpenRouter-generated explanation.")

    presentation_parser = subparsers.add_parser(
        "presentation",
        help="Print the final judge presentation bundle",
    )
    presentation_parser.add_argument("--customer", help="Customer ID to inspect.")
    presentation_parser.add_argument("--scenario", help="Scenario ID from the golden dataset.")
    presentation_parser.add_argument("--role", help="Actor role override.")
    presentation_parser.add_argument("--region", help="Actor region override.")
    presentation_parser.add_argument("--with-llm", action="store_true", help="Include an OpenRouter-generated explanation.")
    presentation_parser.add_argument("--show-details", action="store_true", help="Print analytics breakdowns.")

    args = parser.parse_args()

    if args.command == "generate-data":
        _run_generate_data(settings, args.seed)
        return
    if args.command == "list-scenarios":
        _run_list_scenarios(settings, args.verbose)
        return
    if args.command == "demo":
        _run_demo(settings, args)
        return
    if args.command == "evals":
        _run_evals(settings, args.show_details)
        return
    if args.command == "analytics":
        _run_analytics(settings, args.show_details)
        return
    if args.command == "judge":
        _run_judge(settings, args)
        return
    if args.command == "presentation":
        _run_presentation(settings, args)
        return


def _run_generate_data(settings, seed: int) -> None:
    from cx_agent.ingestion.files import save_customers, save_events, save_events_by_source, write_json
    from cx_agent.ingestion.synthetic import generate_synthetic_dataset

    customers, events, goldens = generate_synthetic_dataset(seed)
    synthetic_root = settings.default_data_dir / "synthetic"
    source_root = synthetic_root / "sources"
    synthetic_root.mkdir(parents=True, exist_ok=True)
    save_customers(synthetic_root / "customers.json", customers)
    save_events(synthetic_root / "events.json", events)
    save_events_by_source(source_root, events, settings)
    write_json(synthetic_root / "goldens.json", goldens)

    print("=" * 72)
    print("Synthetic Data Generated")
    print("=" * 72)
    print(f"Output directory: {_console_safe(synthetic_root)}")
    print(f"Source directory: {_console_safe(source_root)}")
    print(f"Customers: {len(customers)}")
    print(f"Events: {len(events)}")
    print(f"Golden scenarios: {len(goldens)}")


def _run_list_scenarios(settings, verbose: bool) -> None:
    _, _, goldens = load_demo_data(settings.default_data_dir)
    print("=" * 72)
    print("Available Scenarios")
    print("=" * 72)
    for golden in goldens:
        if verbose:
            print(
                f"- {_console_safe(golden['scenario_id'])} | "
                f"customer={_console_safe(golden['customer_id'])} | "
                f"stage={_console_safe(golden['expected_stage'])} | "
                f"category={_console_safe(golden['expected_category'])}"
            )
        else:
            print(f"- {_console_safe(golden['scenario_id'])}")


def _run_demo(settings, args) -> None:
    if not args.customer and not args.scenario:
        raise SystemExit("Provide either --customer or --scenario.")
    if args.customer and args.scenario:
        raise SystemExit("Use either --customer or --scenario, not both.")

    customer_id = args.customer or find_customer_id_by_scenario(settings.default_data_dir, args.scenario)
    result = run_customer_demo(settings, customer_id, args.role, args.region, args.with_llm)

    journey: JourneyResult = result["journey"]
    recommendation: RecommendationResult = result["recommendation"]
    gates: list[GateResult] = result["gates"]
    timeline: list[Event] = result["timeline"]

    print("=" * 72)
    print("Agentic CX Demo Output")
    print("=" * 72)
    print(f"Customer: {_console_safe(result['customer_id'])}")
    print(f"Actor role: {_console_safe(result['actor_role'])}")
    print(f"Actor region: {_console_safe(result['actor_region'])}")
    print(f"Journey stage: {_console_safe(journey.journey_stage)}")
    print(f"Friction points: {_console_safe(', '.join(journey.friction_points))}")
    print(f"Risk label: {_console_safe(journey.risk_label)}")
    print("Evidence:")
    for item in journey.evidence:
        print(f"  - {_console_safe(item)}")
    if args.show_timeline:
        print("Timeline:")
        for event in timeline:
            print(
                "  - "
                f"{_console_safe(event.timestamp)} | "
                f"{_console_safe(event.channel)} | "
                f"{_console_safe(event.event_type)} | "
                f"outcome={_console_safe(event.outcome)}"
            )
    print(f"Recommended action: {_console_safe(recommendation.recommended_action)}")
    print(f"Recommendation category: {_console_safe(recommendation.recommendation_category)}")
    print(f"Rationale: {_console_safe(recommendation.rationale)}")
    print("Verification gates:")
    for gate in gates:
        status = "PASS" if gate.passed else "BLOCK"
        print(f"  - {_console_safe(gate.gate_name)}: {status} | {_console_safe(gate.reason)}")
    print(f"Action allowed: {result['action_allowed']}")
    if result["llm_explanation"] is not None:
        llm_result = result["llm_explanation"]
        print("LLM explanation:")
        print(f"  Used: {llm_result.used}")
        print(f"  Summary: {_console_safe(llm_result.summary)}")
        if llm_result.error:
            print(f"  Error: {_console_safe(llm_result.error)}")
    if result.get("customer_facts") is not None:
        facts_result = result["customer_facts"]
        print("Customer facts:")
        print(f"  Used: {facts_result.used}")
        print(f"  Summary: {_console_safe(facts_result.summary)}")
        print(f"  Problem: {_console_safe(facts_result.problem_statement)}")
        print(f"  Signals: {_console_safe(', '.join(facts_result.source_signals))}")
        print("  Facts:")
        for fact in facts_result.facts:
            print(f"    - {_console_safe(fact)}")
        if facts_result.error:
            print(f"  Error: {_console_safe(facts_result.error)}")
    if result.get("unified_journey") is not None:
        unified_result = result["unified_journey"]
        print("Unified journey:")
        print(f"  Used: {unified_result.used}")
        print(f"  Summary: {_console_safe(unified_result.summary)}")
        print(f"  Signals: {_console_safe(', '.join(unified_result.source_signals))}")
        print("  Touchpoints:")
        for item in unified_result.key_touchpoints:
            print(f"    - {_console_safe(item)}")
        if unified_result.error:
            print(f"  Error: {_console_safe(unified_result.error)}")
    if result.get("judge") is not None:
        judge_result = result["judge"]
        print("Judge score:")
        print(f"  Used: {judge_result.used}")
        print(f"  Score: {int(judge_result.score)}/100")
        print(f"  Passed: {judge_result.passed}")
        print(f"  Summary: {_console_safe(judge_result.summary)}")
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(serialize_demo_result(result), indent=2),
            encoding="utf-8",
        )
        print(f"JSON output written to: {_console_safe(output_path)}")
    print("Audit trail:")
    for entry in result.get("audit_trail", []):
        print(
            "  - "
            f"{_console_safe(entry.step)} | "
            f"{_console_safe(entry.timestamp)} | "
            f"{_console_safe(entry.message)}"
        )
        if getattr(entry, "details", None):
            for key, value in entry.details.items():
                print(f"    { _console_safe(key) }: {_console_safe(value)}")


def _run_evals(settings, show_details: bool) -> None:
    result = run_eval_suite(settings)
    summary = result["summary"]

    print("=" * 72)
    print("Eval Gate Summary")
    print("=" * 72)
    print(f"Total cases: {int(summary['total_cases'])}")
    print(f"Total checks: {int(summary['total_checks'])}")
    print(f"Passed checks: {int(summary['passed_checks'])}")
    print(f"Pass rate: {summary['pass_rate']:.2%}")
    print(f"Eval gate passed: {summary['passed_gate']}")
    if show_details:
        print("Case details:")
        for row in result["details"]:
            print(f"  - {_console_safe(row['scenario_id'])}: {row['scores']}")


def _run_analytics(settings, show_details: bool) -> None:
    result = run_cx_analytics(settings)

    print("=" * 72)
    print("CX Analytics Summary")
    print("=" * 72)
    totals = result["totals"]
    print(f"Customers: {int(totals['customers'])}")
    print(f"Events: {int(totals['events'])}")
    print(f"Golden scenarios: {int(totals['golden_scenarios'])}")
    print(f"Source buckets: {int(totals['source_buckets'])}")
    print(f"Channels: {int(totals['channels'])}")
    if show_details:
        print("Source counts:")
        for key, value in result["source_counts"].items():
            print(f"  - {_console_safe(key)}: {int(value)}")
        print("Channel counts:")
        for key, value in result["channel_counts"].items():
            print(f"  - {_console_safe(key)}: {int(value)}")
        print("Journey stages:")
        for key, value in result["stage_counts"].items():
            print(f"  - {_console_safe(key)}: {int(value)}")
        print("Risk labels:")
        for key, value in result["risk_counts"].items():
            print(f"  - {_console_safe(key)}: {int(value)}")
        print("Friction labels:")
        for key, value in result["friction_counts"].items():
            print(f"  - {_console_safe(key)}: {int(value)}")


def _run_judge(settings, args) -> None:
    if not args.customer and not args.scenario:
        raise SystemExit("Provide either --customer or --scenario.")
    if args.customer and args.scenario:
        raise SystemExit("Use either --customer or --scenario, not both.")

    customer_id = args.customer or find_customer_id_by_scenario(settings.default_data_dir, args.scenario)
    result = run_judge_review(settings, customer_id, args.role, args.region, args.with_llm)
    judge = result["judge"]

    print("=" * 72)
    print("Judge Review")
    print("=" * 72)
    print(f"Customer: {_console_safe(result['customer_id'])}")
    print(f"Actor role: {_console_safe(result['actor_role'])}")
    print(f"Actor region: {_console_safe(result['actor_region'])}")
    print(f"Governance status: {_console_safe(result['governance_status'])}")
    print(f"Decision summary: {_console_safe(result['decision_summary'])}")
    print(f"Safe next step: {_console_safe(result['safe_next_step'])}")
    print(f"Judge score: {int(judge['score'])}/100")
    print(f"Judge passed: {judge['passed']}")
    print(f"Judge summary: {_console_safe(judge['summary'])}")
    if judge.get("error"):
        print(f"Judge backend note: {_console_safe(judge['error'])}")


def _run_presentation(settings, args) -> None:
    if not args.customer and not args.scenario:
        raise SystemExit("Provide either --customer or --scenario.")
    if args.customer and args.scenario:
        raise SystemExit("Use either --customer or --scenario, not both.")

    customer_id = args.customer or find_customer_id_by_scenario(settings.default_data_dir, args.scenario)
    bundle = run_presentation(settings, customer_id, args.role, args.region, args.with_llm)
    demo = bundle["demo"]
    analytics = bundle["analytics"]
    judge = bundle["judge"]

    print("=" * 72)
    print("Final Judge Presentation")
    print("=" * 72)
    print(f"Summary: {_console_safe(bundle['presentation_summary'])}")
    print("")
    _print_demo_section(demo, args.show_details)
    print("")
    _print_analytics_section(analytics, args.show_details)
    print("")
    print("Judge Score:")
    print(f"  Score: {int(judge['score'])}/100")
    print(f"  Passed: {judge['passed']}")
    print(f"  Summary: {_console_safe(judge['summary'])}")
    if judge.get("error"):
        print(f"  Backend note: {_console_safe(judge['error'])}")


def _print_demo_section(demo: dict[str, object], show_details: bool) -> None:
    journey = demo["journey"]
    recommendation = demo["recommendation"]
    gates = demo["gates"]
    print("Customer Story:")
    print(f"  Customer: {_console_safe(demo['customer_id'])}")
    print(f"  Actor role: {_console_safe(demo['actor_role'])}")
    print(f"  Actor region: {_console_safe(demo['actor_region'])}")
    print(f"  Journey stage: {_console_safe(journey['journey_stage'])}")
    print(f"  Friction points: {_console_safe(', '.join(journey['friction_points']))}")
    print(f"  Risk label: {_console_safe(journey['risk_label'])}")
    print(f"  Recommended action: {_console_safe(recommendation['recommended_action'])}")
    print(f"  Recommendation category: {_console_safe(recommendation['recommendation_category'])}")
    print(f"  Action allowed: {demo['action_allowed']}")
    print(f"  Judge score: {int(demo['judge']['score'])}/100")
    if demo.get("customer_facts"):
        facts = demo["customer_facts"]
        print(f"  Customer problem: {_console_safe(facts['problem_statement'])}")
        print(f"  Customer facts: {_console_safe('; '.join(facts['facts']))}")
    if show_details:
        print("  Evidence:")
        for item in journey["evidence"]:
            print(f"    - {_console_safe(item)}")
        print("  Gates:")
        for gate in gates:
            status = "PASS" if gate["passed"] else "BLOCK"
            print(f"    - {_console_safe(gate['gate_name'])}: {status} | {_console_safe(gate['reason'])}")
        print("  Audit trail:")
        for entry in demo.get("audit_trail", []):
            print(f"    - {_console_safe(entry['step'])} | {_console_safe(entry['message'])}")
            if entry.get("details"):
                for key, value in entry["details"].items():
                    print(f"      {_console_safe(key)}: {_console_safe(value)}")


def _print_analytics_section(analytics: dict[str, object], show_details: bool) -> None:
    totals = analytics["totals"]
    print("CX Analytics:")
    print(f"  Customers: {int(totals['customers'])}")
    print(f"  Events: {int(totals['events'])}")
    print(f"  Golden scenarios: {int(totals['golden_scenarios'])}")
    print(f"  Source buckets: {int(totals['source_buckets'])}")
    print(f"  Channels: {int(totals['channels'])}")
    if show_details:
        print("  Source counts:")
        for key, value in analytics["source_counts"].items():
            print(f"    - {_console_safe(key)}: {int(value)}")
        print("  Journey stages:")
        for key, value in analytics["stage_counts"].items():
            print(f"    - {_console_safe(key)}: {int(value)}")
        print("  Risk labels:")
        for key, value in analytics["risk_counts"].items():
            print(f"    - {_console_safe(key)}: {int(value)}")
        print("  Friction labels:")
        for key, value in analytics["friction_counts"].items():
            print(f"    - {_console_safe(key)}: {int(value)}")


if __name__ == "__main__":
    main()

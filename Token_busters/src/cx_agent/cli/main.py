from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cx_agent.models import Event, GateResult, JourneyResult, RecommendationResult
from cx_agent.orchestration.pipeline import (
    find_customer_id_by_scenario,
    load_demo_data,
    run_customer_demo,
    run_eval_suite,
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


def _run_generate_data(settings, seed: int) -> None:
    from cx_agent.ingestion.files import save_customers, save_events, write_json
    from cx_agent.ingestion.synthetic import generate_synthetic_dataset

    customers, events, goldens = generate_synthetic_dataset(seed)
    synthetic_root = settings.default_data_dir / "synthetic"
    synthetic_root.mkdir(parents=True, exist_ok=True)
    save_customers(synthetic_root / "customers.json", customers)
    save_events(synthetic_root / "events.json", events)
    write_json(synthetic_root / "goldens.json", goldens)

    print("=" * 72)
    print("Synthetic Data Generated")
    print("=" * 72)
    print(f"Output directory: {_console_safe(synthetic_root)}")
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
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(serialize_demo_result(result), indent=2),
            encoding="utf-8",
        )
        print(f"JSON output written to: {_console_safe(output_path)}")


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


if __name__ == "__main__":
    main()

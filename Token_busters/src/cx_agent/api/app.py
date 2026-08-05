from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, Response

from cx_agent.api.models import (
    DemoResponse,
    EvalResponse,
    HealthResponse,
    ScenarioListResponse,
    TimelineResponse,
)
from cx_agent.orchestration.pipeline import (
    find_customer_id_by_scenario,
    load_demo_data,
    run_customer_demo,
    run_eval_suite,
    serialize_demo_result,
)
from cx_agent.settings import load_settings


app = FastAPI(
    title="Agentic CX API",
    version="0.1.0",
    description="Backend API for governed customer journey intelligence demos.",
    contact={"name": "Token Busters"},
    openapi_tags=[
        {"name": "system", "description": "Health and service metadata."},
        {"name": "journeys", "description": "Journey demos and timeline inspection."},
        {"name": "evaluation", "description": "Golden-case evaluation endpoints."},
    ],
)


@app.get("/", tags=["system"])
def root() -> dict[str, object]:
    return {
        "message": "Agentic CX API is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "scenarios_url": "/scenarios",
        "demo_url": "/demo?scenario_id=onboarding_abandonment",
        "timeline_url": "/timeline?scenario_id=onboarding_abandonment",
        "evals_url": "/evals",
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health", response_model=HealthResponse, tags=["system"], summary="Check service health")
def health() -> HealthResponse:
    settings = load_settings()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        llm_enabled=settings.enable_llm,
        eval_gate_enabled=settings.enable_eval_gate,
    )


@app.get("/scenarios", response_model=ScenarioListResponse, tags=["journeys"], summary="List demo scenarios")
def list_scenarios() -> ScenarioListResponse:
    settings = load_settings()
    _, _, goldens = load_demo_data(settings.default_data_dir)
    return ScenarioListResponse(scenarios=goldens)


@app.get(
    "/demo",
    response_model=DemoResponse,
    tags=["journeys"],
    summary="Run a governed journey demo",
)
def demo(
    customer_id: str | None = Query(default=None),
    scenario_id: str | None = Query(default=None),
    actor_role: str | None = Query(default=None),
    actor_region: str | None = Query(default=None),
    include_llm: bool = Query(default=False),
) -> DemoResponse:
    serialized = _resolve_demo_payload(customer_id, scenario_id, actor_role, actor_region, include_llm)
    return DemoResponse(**_decorate_demo_payload(serialized))


@app.get(
    "/timeline",
    response_model=TimelineResponse,
    tags=["journeys"],
    summary="Return the event timeline for a customer or scenario",
)
def timeline(
    customer_id: str | None = Query(default=None),
    scenario_id: str | None = Query(default=None),
    actor_role: str | None = Query(default=None),
    actor_region: str | None = Query(default=None),
) -> TimelineResponse:
    serialized = _resolve_demo_payload(customer_id, scenario_id, actor_role, actor_region, include_llm=False)
    return TimelineResponse(
        customer_id=serialized["customer_id"],
        scenario_id=scenario_id,
        actor_role=serialized["actor_role"],
        actor_region=serialized["actor_region"],
        journey_stage=serialized["journey"]["journey_stage"],
        timeline=serialized["timeline"],
    )


@app.get("/evals", response_model=EvalResponse, tags=["evaluation"], summary="Run golden-case evals")
def evals() -> EvalResponse:
    settings = load_settings()
    return EvalResponse(**run_eval_suite(settings))


def _resolve_demo_payload(
    customer_id: str | None,
    scenario_id: str | None,
    actor_role: str | None,
    actor_region: str | None,
    include_llm: bool,
) -> dict[str, object]:
    if not customer_id and not scenario_id:
        raise HTTPException(status_code=400, detail="Provide either customer_id or scenario_id.")
    if customer_id and scenario_id:
        raise HTTPException(status_code=400, detail="Use either customer_id or scenario_id, not both.")

    settings = load_settings()
    try:
        resolved_customer_id = customer_id or find_customer_id_by_scenario(
            settings.default_data_dir,
            scenario_id or "",
        )
        result = run_customer_demo(
            settings,
            resolved_customer_id,
            actor_role=actor_role,
            actor_region=actor_region,
            include_llm=include_llm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return serialize_demo_result(result)


def _decorate_demo_payload(serialized: dict[str, object]) -> dict[str, object]:
    gates = serialized["gates"]
    blocked_reasons = [gate["reason"] for gate in gates if not gate["passed"]]
    action_allowed = bool(serialized["action_allowed"])
    governance_status = "allowed" if action_allowed else "blocked"

    if action_allowed:
        safe_next_step = "The action passed governance checks and can proceed through an approved workflow."
    else:
        gate_names = [gate["gate_name"] for gate in gates if not gate["passed"]]
        if "ownership" in gate_names and "capability" in gate_names:
            safe_next_step = "Use an authorized actor with both the correct ownership scope and the required action capability."
        elif "ownership" in gate_names:
            safe_next_step = "Route this case to an actor who owns the customer's region or account scope."
        else:
            safe_next_step = "Route this action to a role that is allowed to perform the recommended intervention."

    decision_summary = _build_decision_summary(serialized, governance_status, safe_next_step)
    enriched = dict(serialized)
    enriched["governance_status"] = governance_status
    enriched["blocked_reasons"] = blocked_reasons
    enriched["safe_next_step"] = safe_next_step
    enriched["decision_summary"] = decision_summary
    return enriched


def _build_decision_summary(
    serialized: dict[str, object],
    governance_status: str,
    safe_next_step: str,
) -> str:
    journey = serialized["journey"]
    recommendation = serialized["recommendation"]
    if governance_status == "allowed":
        return (
            f"Customer {serialized['customer_id']} is in stage {journey['journey_stage']} with "
            f"risk {journey['risk_label']}. The recommended action is "
            f"{recommendation['recommendation_category']} and it passed governance checks."
        )
    return (
        f"Customer {serialized['customer_id']} is in stage {journey['journey_stage']} with "
        f"risk {journey['risk_label']}. The recommended action is "
        f"{recommendation['recommendation_category']}, but it is blocked by governance checks. "
        f"{safe_next_step}"
    )


def run() -> None:
    import uvicorn

    uvicorn.run("cx_agent.api.app:app", host="127.0.0.1", port=8000, reload=False)

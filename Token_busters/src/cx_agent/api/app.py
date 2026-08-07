from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from cx_agent.api.models import (
    AnalyticsResponse,
    DemoResponse,
    EvalResponse,
    HealthResponse,
    JudgeReviewResponse,
    PresentationResponse,
    ScenarioListResponse,
    TimelineResponse,
)
from cx_agent.orchestration.pipeline import (
    decorate_demo_payload,
    find_customer_id_by_scenario,
    load_demo_data,
    run_cx_analytics,
    run_customer_demo,
    run_eval_suite,
    run_judge_review,
    run_presentation,
    serialize_demo_result,
)
from cx_agent.settings import Settings, load_settings


STATIC_DIR = Path(__file__).resolve().parent / "static"


app = FastAPI(
    title="Agentic CX API",
    version="0.1.0",
    description="Backend API for governed customer journey intelligence demos.",
    contact={"name": "Token Busters"},
    openapi_tags=[
        {"name": "system", "description": "Health and service metadata."},
        {"name": "journeys", "description": "Journey demos and timeline inspection."},
        {"name": "analytics", "description": "CX summary and source coverage."},
        {"name": "evaluation", "description": "Golden-case evaluation endpoints."},
    ],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", tags=["system"])
def root() -> dict[str, object]:
    return {
        "message": "Agentic CX API is running.",
        "docs_url": "/docs",
        "ui_url": "/ui",
        "health_url": "/health",
        "scenarios_url": "/scenarios",
        "analytics_url": "/analytics",
        "demo_url": "/demo?scenario_id=onboarding_abandonment",
        "timeline_url": "/timeline?scenario_id=onboarding_abandonment",
        "judge_url": "/judge?scenario_id=renewal_risk",
        "presentation_url": "/presentation?scenario_id=renewal_risk",
        "evals_url": "/evals",
    }


@app.get("/ui", include_in_schema=False)
def ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


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


@app.get("/analytics", response_model=AnalyticsResponse, tags=["analytics"], summary="Summarize CX coverage and patterns")
def analytics() -> AnalyticsResponse:
    settings = load_settings()
    return AnalyticsResponse(**run_cx_analytics(settings))


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
    return DemoResponse(**decorate_demo_payload(serialized))


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


@app.get("/judge", response_model=JudgeReviewResponse, tags=["evaluation"], summary="Run the judge score only")
def judge(
    customer_id: str | None = Query(default=None),
    scenario_id: str | None = Query(default=None),
    actor_role: str | None = Query(default=None),
    actor_region: str | None = Query(default=None),
    include_llm: bool = Query(default=False),
) -> JudgeReviewResponse:
    settings = load_settings()
    try:
        resolved_customer_id = _resolve_customer_id(settings, customer_id, scenario_id)
        review = run_judge_review(
            settings,
            resolved_customer_id,
            actor_role=actor_role,
            actor_region=actor_region,
            include_llm=include_llm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return JudgeReviewResponse(**review)


@app.get("/presentation", response_model=PresentationResponse, tags=["evaluation"], summary="Run the final judge presentation bundle")
def presentation(
    customer_id: str | None = Query(default=None),
    scenario_id: str | None = Query(default=None),
    actor_role: str | None = Query(default=None),
    actor_region: str | None = Query(default=None),
    include_llm: bool = Query(default=False),
) -> PresentationResponse:
    settings = load_settings()
    try:
        resolved_customer_id = _resolve_customer_id(settings, customer_id, scenario_id)
        bundle = run_presentation(
            settings,
            resolved_customer_id,
            actor_role=actor_role,
            actor_region=actor_region,
            include_llm=include_llm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PresentationResponse(**bundle)


def _resolve_demo_payload(
    customer_id: str | None,
    scenario_id: str | None,
    actor_role: str | None,
    actor_region: str | None,
    include_llm: bool,
) -> dict[str, object]:
    settings = load_settings()
    try:
        resolved_customer_id = _resolve_customer_id(settings, customer_id, scenario_id)
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


def _resolve_customer_id(settings: Settings, customer_id: str | None, scenario_id: str | None) -> str:
    if not customer_id and not scenario_id:
        raise HTTPException(status_code=400, detail="Provide either customer_id or scenario_id.")
    if customer_id and scenario_id:
        raise HTTPException(status_code=400, detail="Use either customer_id or scenario_id, not both.")
    return customer_id or find_customer_id_by_scenario(settings.default_data_dir, scenario_id or "")


def run() -> None:
    import uvicorn

    uvicorn.run("cx_agent.api.app:app", host="127.0.0.1", port=8000, reload=False)

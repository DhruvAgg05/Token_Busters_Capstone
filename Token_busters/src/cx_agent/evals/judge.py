from __future__ import annotations

from cx_agent.llm.openrouter import LLMExplanationResult, generate_judge_commentary
from cx_agent.models import JudgeResult
from cx_agent.settings import Settings


def judge_demo_output(settings: Settings, demo_payload: dict[str, object]) -> JudgeResult:
    criteria = {
        "evidence_backed": bool(demo_payload.get("journey", {}).get("evidence")),
        "privacy_preserved": _privacy_preserved(demo_payload),
        "governance_explained": bool(demo_payload.get("action_allowed")),
        "audit_traced": bool(demo_payload.get("audit_trail")),
        "decision_clear": bool(demo_payload.get("journey", {}).get("journey_stage"))
        and bool(demo_payload.get("recommendation", {}).get("recommended_action")),
    }
    score = sum(1 for passed in criteria.values() if passed) * 20
    passed = score >= 80
    summary = _fallback_summary(score, criteria, passed)
    llm_result: LLMExplanationResult | None = None

    if settings.enable_llm:
        llm_result = generate_judge_commentary(settings, demo_payload, score, criteria)
        if llm_result.used:
            summary = llm_result.summary

    return JudgeResult(
        enabled=settings.enable_llm,
        used=bool(llm_result and llm_result.used),
        score=score,
        passed=passed,
        summary=summary,
        criteria=criteria,
        error=None if llm_result is None else _normalize_error(llm_result.error),
    )


def _privacy_preserved(demo_payload: dict[str, object]) -> bool:
    customer_id = str(demo_payload.get("customer_id", ""))
    if not customer_id.startswith("CUST_MASKED_"):
        return False
    for event in demo_payload.get("timeline", []):
        if "name" in event:
            return False
    return True


def _fallback_summary(score: int, criteria: dict[str, bool], passed: bool) -> str:
    passed_items = [name for name, ok in criteria.items() if ok]
    failed_items = [name for name, ok in criteria.items() if not ok]
    status = "passes" if passed else "needs work"
    return (
        f"Judge score {score}/100. The demo {status} because it satisfies {', '.join(passed_items)}"
        + (f" and still needs {', '.join(failed_items)}." if failed_items else ".")
    )


def _normalize_error(error: str | None) -> str | None:
    if error is None:
        return None
    if error == "missing_api_key":
        return error
    return "llm_request_failed"

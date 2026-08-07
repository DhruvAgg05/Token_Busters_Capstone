from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from cx_agent.models import GateResult, JourneyResult, RecommendationResult
from cx_agent.settings import Settings


@dataclass
class LLMExplanationResult:
    enabled: bool
    used: bool
    summary: str
    error: str | None = None


def generate_explanation(
    settings: Settings,
    customer_id: str,
    journey: JourneyResult,
    recommendation: RecommendationResult,
    gates: list[GateResult],
    action_allowed: bool,
) -> LLMExplanationResult:
    if not settings.enable_llm:
        return LLMExplanationResult(
            enabled=False,
            used=False,
            summary="LLM explanations are disabled in configuration.",
        )

    if not settings.openrouter_api_key:
        return LLMExplanationResult(
            enabled=True,
            used=False,
            summary="LLM explanation skipped because no OpenRouter API key is configured.",
            error="missing_api_key",
        )

    prompt = _build_prompt(customer_id, journey, recommendation, gates, action_allowed)
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a secure CX operations copilot. "
                    "Use only the provided evidence. "
                    "Do not reveal PII. "
                    "Do not invent causes, permissions, or actions. "
                    "If a gate is blocked, clearly state that the action must not proceed."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_site_url,
        "X-Title": settings.openrouter_app_name,
    }

    try:
        response_json = _post_json(
            f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
            payload,
            headers,
            timeout_seconds=settings.openrouter_timeout_seconds,
        )
        content = (
            response_json.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not content:
            return LLMExplanationResult(
                enabled=True,
                used=False,
                summary="LLM explanation returned an empty response.",
                error="empty_response",
            )
        return LLMExplanationResult(enabled=True, used=True, summary=content)
    except Exception as exc:
        return LLMExplanationResult(
            enabled=True,
            used=False,
            summary="LLM explanation could not be generated, so the rule-based result is shown instead.",
            error=str(exc),
        )


def generate_judge_commentary(
    settings: Settings,
    demo_payload: dict[str, Any],
    score: int,
    criteria: dict[str, bool],
) -> LLMExplanationResult:
    if not settings.enable_llm:
        return LLMExplanationResult(
            enabled=False,
            used=False,
            summary="LLM judging is disabled in configuration.",
        )

    if not settings.openrouter_api_key:
        return LLMExplanationResult(
            enabled=True,
            used=False,
            summary="LLM judge skipped because no OpenRouter API key is configured.",
            error="missing_api_key",
        )

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict but concise CX demo judge. "
                    "Assess the output for evidence use, governance safety, privacy protection, and clarity. "
                    "Do not invent details. "
                    "Return one short paragraph with your assessment."
                ),
            },
            {"role": "user", "content": _build_judge_prompt(demo_payload, score, criteria)},
        ],
        "temperature": 0.1,
    }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_site_url,
        "X-Title": settings.openrouter_app_name,
    }

    try:
        response_json = _post_json(
            f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
            payload,
            headers,
            timeout_seconds=settings.openrouter_timeout_seconds,
        )
        content = (
            response_json.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not content:
            return LLMExplanationResult(
                enabled=True,
                used=False,
                summary="LLM judge returned an empty response.",
                error="empty_response",
            )
        return LLMExplanationResult(enabled=True, used=True, summary=content)
    except Exception as exc:
        return LLMExplanationResult(
            enabled=True,
            used=False,
            summary="LLM judge could not be generated, so the rule-based score is shown instead.",
            error=str(exc),
        )


def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout_seconds: float,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method="POST")
    with request.urlopen(req, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw)


def _build_prompt(
    customer_id: str,
    journey: JourneyResult,
    recommendation: RecommendationResult,
    gates: list[GateResult],
    action_allowed: bool,
) -> str:
    gate_lines = [
        f"- {gate.gate_name}: {'PASS' if gate.passed else 'BLOCK'} | {gate.reason}" for gate in gates
    ]
    evidence_lines = [f"- {item}" for item in journey.evidence]
    return f"""
Summarize this governed CX decision for a terminal demo.

Constraints:
- Keep it under 120 words.
- Use only the supplied evidence.
- Do not reveal any personal details beyond the masked customer ID.
- If action_allowed is false, explain that the action is blocked and mention the safe next step.

Masked customer ID: {customer_id}
Journey stage: {journey.journey_stage}
Friction points: {", ".join(journey.friction_points)}
Risk label: {journey.risk_label}
Recommendation category: {recommendation.recommendation_category}
Recommended action: {recommendation.recommended_action}
Rationale: {recommendation.rationale}
Action allowed: {action_allowed}
Verification gates:
{chr(10).join(gate_lines)}
Evidence:
{chr(10).join(evidence_lines)}
""".strip()


def _build_judge_prompt(
    demo_payload: dict[str, Any],
    score: int,
    criteria: dict[str, bool],
) -> str:
    criterion_lines = [f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in criteria.items()]
    audit_lines = [f"- {entry['step']}: {entry['message']}" for entry in demo_payload.get("audit_trail", [])]
    journey = demo_payload["journey"]
    recommendation = demo_payload["recommendation"]
    decision_summary = demo_payload.get("decision_summary") or (
        f"Customer {demo_payload['customer_id']} is in stage {journey['journey_stage']} with risk {journey['risk_label']}. "
        f"The recommended action is {recommendation['recommendation_category']}."
    )
    return f"""
Judge this CX demo output using only the supplied data.

Score: {score}/100

Criteria:
{chr(10).join(criterion_lines)}

Customer: {demo_payload["customer_id"]}
Journey stage: {journey["journey_stage"]}
Risk label: {journey["risk_label"]}
Action allowed: {demo_payload["action_allowed"]}
Decision summary: {decision_summary}
Recommended category: {recommendation["recommendation_category"]}

Audit trail:
{chr(10).join(audit_lines)}

Return one short paragraph that says whether this is a strong, safe, evidence-backed demo output.
""".strip()

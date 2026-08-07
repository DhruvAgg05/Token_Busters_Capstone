from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import request

from cx_agent.models import CustomerFactSummary, CustomerProfile, GateResult, JudgeResult, JourneyResult, RecommendationResult, UnifiedJourneyView
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

    try:
        content = _post_chat_completion(settings, payload)
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
            summary="LLM explanation could not be generated, so the governed pipeline result is shown without an LLM narrative.",
            error=str(exc),
        )


def generate_judge_assessment(
    settings: Settings,
    demo_payload: dict[str, Any],
) -> JudgeResult:
    fallback = _build_judge_fallback(demo_payload)
    if not settings.enable_llm:
        return JudgeResult(
            enabled=False,
            used=False,
            score=fallback["score"],
            passed=fallback["passed"],
            summary=fallback["summary"],
            criteria=fallback["criteria"],
            error="llm_disabled",
        )

    if not settings.openrouter_api_key:
        return JudgeResult(
            enabled=True,
            used=False,
            score=fallback["score"],
            passed=fallback["passed"],
            summary=fallback["summary"],
            criteria=fallback["criteria"],
            error="missing_api_key",
        )

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict CX demo judge. "
                    "Score the demo for evidence use, privacy, governance clarity, auditability, and decision clarity. "
                    "Use only the provided evidence. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": _build_judge_assessment_prompt(demo_payload)},
        ],
        "temperature": 0.0,
    }

    try:
        content = _post_chat_completion(settings, payload)
        parsed = _parse_judge_assessment_response(content)
        if parsed is None:
            return JudgeResult(
                enabled=True,
                used=False,
                score=fallback["score"],
                passed=fallback["passed"],
                summary=fallback["summary"],
                criteria=fallback["criteria"],
                error="invalid_json_response",
            )
        score = max(0, min(100, int(parsed["score"])))
        criteria = {key: bool(value) for key, value in parsed["criteria"].items()}
        passed = bool(parsed.get("passed", score >= 80))
        return JudgeResult(
            enabled=True,
            used=True,
            score=score,
            passed=passed,
            summary=str(parsed["summary"]),
            criteria=criteria,
        )
    except Exception as exc:
        return JudgeResult(
            enabled=True,
            used=False,
            score=fallback["score"],
            passed=fallback["passed"],
            summary=fallback["summary"],
            criteria=fallback["criteria"],
            error=str(exc),
        )


def generate_customer_fact_summary(
    settings: Settings,
    demo_payload: dict[str, Any],
) -> CustomerFactSummary:
    fallback = _build_customer_fact_fallback(demo_payload)
    if not settings.enable_llm:
        return CustomerFactSummary(
            enabled=False,
            used=False,
            summary=fallback["summary"],
            problem_statement=fallback["problem_statement"],
            facts=fallback["facts"],
            source_signals=fallback["source_signals"],
            error="llm_disabled",
        )

    if not settings.openrouter_api_key:
        return CustomerFactSummary(
            enabled=True,
            used=False,
            summary=fallback["summary"],
            problem_statement=fallback["problem_statement"],
            facts=fallback["facts"],
            source_signals=fallback["source_signals"],
            error="missing_api_key",
        )

    prompt = _build_fact_prompt(demo_payload)
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a secure CX evidence summarizer. "
                    "Condense the merged customer journey into short factual bullets. "
                    "Do not include complete conversations, quoted text, or personal data. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }

    try:
        content = _post_chat_completion(settings, payload)
        parsed = _parse_fact_response(content)
        if parsed is None:
            return CustomerFactSummary(
                enabled=True,
                used=False,
                summary=fallback["summary"],
                problem_statement=fallback["problem_statement"],
                facts=fallback["facts"],
                source_signals=fallback["source_signals"],
                error="invalid_json_response",
            )
        return CustomerFactSummary(
            enabled=True,
            used=True,
            summary=parsed["summary"],
            problem_statement=parsed["problem_statement"],
            facts=parsed["facts"],
            source_signals=parsed["source_signals"],
        )
    except Exception as exc:
        return CustomerFactSummary(
            enabled=True,
            used=False,
            summary=fallback["summary"],
            problem_statement=fallback["problem_statement"],
            facts=fallback["facts"],
            source_signals=fallback["source_signals"],
            error=str(exc),
        )


def generate_source_bucket_label(
    settings: Settings,
    event_payload: dict[str, Any],
) -> tuple[str, bool, str | None]:
    allowed_labels = {"web", "app", "support", "payments", "communications", "surveys"}
    fallback_label = _fallback_source_bucket(str(event_payload.get("channel", "unknown")))
    if not settings.enable_llm:
        return fallback_label, False, "llm_disabled"

    if not settings.openrouter_api_key:
        return fallback_label, False, "missing_api_key"

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You classify customer events into a single source bucket. "
                    "Choose only one label from: web, app, support, payments, communications, surveys. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": _build_source_bucket_prompt(event_payload),
            },
        ],
        "temperature": 0.0,
    }

    try:
        content = _post_chat_completion(settings, payload)
        parsed = _parse_source_bucket_response(content)
        if parsed not in allowed_labels:
            return fallback_label, False, "invalid_response"
        return parsed, True, None
    except Exception as exc:
        return fallback_label, False, str(exc)


def generate_unified_journey_view(
    settings: Settings,
    demo_payload: dict[str, Any],
) -> UnifiedJourneyView:
    fallback = _build_unified_journey_fallback(demo_payload)
    if not settings.enable_llm:
        return UnifiedJourneyView(
            enabled=False,
            used=False,
            summary=fallback["summary"],
            key_touchpoints=fallback["key_touchpoints"],
            source_signals=fallback["source_signals"],
            error="llm_disabled",
        )

    if not settings.openrouter_api_key:
        return UnifiedJourneyView(
            enabled=True,
            used=False,
            summary=fallback["summary"],
            key_touchpoints=fallback["key_touchpoints"],
            source_signals=fallback["source_signals"],
            error="missing_api_key",
        )

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a CX journey synthesizer. "
                    "Merge the provided touchpoints into one short, human-readable journey view. "
                    "Do not quote raw messages or reveal personal data. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": _build_unified_journey_prompt(demo_payload)},
        ],
        "temperature": 0.1,
    }

    try:
        content = _post_chat_completion(settings, payload)
        parsed = _parse_unified_journey_response(content)
        if parsed is None:
            return UnifiedJourneyView(
                enabled=True,
                used=False,
                summary=fallback["summary"],
                key_touchpoints=fallback["key_touchpoints"],
                source_signals=fallback["source_signals"],
                error="invalid_json_response",
            )
        return UnifiedJourneyView(
            enabled=True,
            used=True,
            summary=parsed["summary"],
            key_touchpoints=parsed["key_touchpoints"],
            source_signals=parsed["source_signals"],
        )
    except Exception as exc:
        return UnifiedJourneyView(
            enabled=True,
            used=False,
            summary=fallback["summary"],
            key_touchpoints=fallback["key_touchpoints"],
            source_signals=fallback["source_signals"],
            error=str(exc),
        )


def generate_customer_profile(
    settings: Settings,
    customer: Any,
    timeline: list[Any],
    journey: JourneyResult,
) -> tuple[CustomerProfile, bool, str | None]:
    fallback = _build_customer_profile_fallback(customer, journey)
    if not settings.enable_llm:
        return fallback, False, "llm_disabled"

    if not settings.openrouter_api_key:
        return fallback, False, "missing_api_key"

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a CX personalization assistant. "
                    "Convert the customer journey into a concise profile. "
                    "Do not invent facts, do not reveal PII, and return valid JSON only."
                ),
            },
            {"role": "user", "content": _build_customer_profile_prompt(customer, timeline, journey)},
        ],
        "temperature": 0.1,
    }

    try:
        content = _post_chat_completion(settings, payload)
        parsed = _parse_customer_profile_response(content)
        if parsed is None:
            return fallback, False, "invalid_json_response"
        return CustomerProfile(**parsed), True, None
    except Exception as exc:
        return fallback, False, str(exc)


def generate_recommendation(
    settings: Settings,
    customer: Any,
    profile: CustomerProfile,
    journey: JourneyResult,
) -> tuple[RecommendationResult, bool, str | None]:
    fallback = _build_recommendation_fallback(customer, profile, journey)
    if not settings.enable_llm:
        return fallback, False, "llm_disabled"

    if not settings.openrouter_api_key:
        return fallback, False, "missing_api_key"

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a CX recommendation assistant. "
                    "Choose the safest next best action from the evidence provided. "
                    "Do not invent actions or business rules. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": _build_recommendation_prompt(customer, profile, journey)},
        ],
        "temperature": 0.1,
    }

    try:
        content = _post_chat_completion(settings, payload)
        parsed = _parse_recommendation_response(content)
        if parsed is None:
            return fallback, False, "invalid_json_response"
        return RecommendationResult(**parsed), True, None
    except Exception as exc:
        return fallback, False, str(exc)


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


def _post_chat_completion(settings: Settings, payload: dict[str, Any]) -> str:
    response_json = _post_json(
        f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
        payload,
        {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        },
        timeout_seconds=settings.openrouter_timeout_seconds,
    )
    return (
        response_json.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )


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


def _build_judge_assessment_prompt(demo_payload: dict[str, Any]) -> str:
    journey = demo_payload["journey"]
    recommendation = demo_payload["recommendation"]
    customer_facts = demo_payload.get("customer_facts") or {}
    unified_journey = demo_payload.get("unified_journey") or {}
    audit_lines = [f"- {entry['step']}: {entry['message']}" for entry in demo_payload.get("audit_trail", [])]
    evidence_lines = [f"- {item}" for item in journey.get("evidence", [])]
    return f"""
Judge this CX demo output and assign a score from 0 to 100.

Rules:
- Use only the supplied evidence.
- Be strict but fair.
- Penalize missing privacy, weak governance, weak auditability, or unclear decisions.
- Return JSON with exactly these keys: score, passed, summary, criteria.
- criteria must include exactly these keys: evidence_backed, privacy_preserved, governance_explained, audit_traced, decision_clear.

Customer ID: {demo_payload["customer_id"]}
Journey stage: {journey["journey_stage"]}
Risk label: {journey["risk_label"]}
Action allowed: {demo_payload["action_allowed"]}
Decision summary: {demo_payload.get("decision_summary", "")}
Customer facts summary: {customer_facts.get("summary", "unknown")}
Unified journey summary: {unified_journey.get("summary", "unknown")}
Recommended action: {recommendation["recommended_action"]}
Rationale: {recommendation["rationale"]}
Audit trail:
{chr(10).join(audit_lines)}
Evidence:
{chr(10).join(evidence_lines)}

Desired JSON shape:
{{
  "score": 90,
  "passed": true,
  "summary": "One short verdict sentence.",
  "criteria": {{
    "evidence_backed": true,
    "privacy_preserved": true,
    "governance_explained": true,
    "audit_traced": true,
    "decision_clear": true
  }}
}}
""".strip()


def _parse_judge_assessment_response(content: str) -> dict[str, Any] | None:
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    parsed = _try_parse_json(candidate)
    if parsed is None:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = _try_parse_json(candidate[start : end + 1])
    if not isinstance(parsed, dict):
        return None

    try:
        score = int(parsed.get("score", -1))
    except Exception:
        return None
    summary = str(parsed.get("summary", "")).strip()
    criteria = parsed.get("criteria", {})
    if not summary or not isinstance(criteria, dict):
        return None
    normalized_criteria = {
        "evidence_backed": bool(criteria.get("evidence_backed", False)),
        "privacy_preserved": bool(criteria.get("privacy_preserved", False)),
        "governance_explained": bool(criteria.get("governance_explained", False)),
        "audit_traced": bool(criteria.get("audit_traced", False)),
        "decision_clear": bool(criteria.get("decision_clear", False)),
    }
    passed = bool(parsed.get("passed", score >= 80))
    return {
        "score": score,
        "passed": passed,
        "summary": summary,
        "criteria": normalized_criteria,
    }


def _build_fact_prompt(demo_payload: dict[str, Any]) -> str:
    journey = demo_payload["journey"]
    recommendation = demo_payload["recommendation"]
    profile = demo_payload["profile"]
    timeline = demo_payload.get("timeline", [])
    source_signals = sorted({str(event.get("channel", "unknown")) for event in timeline})
    evidence = journey.get("evidence", [])
    audit_steps = [entry.get("step", "") for entry in demo_payload.get("audit_trail", [])]
    return f"""
Summarize the merged customer case into structured facts.

Rules:
- Do not quote full messages or conversations.
- Do not include personal identifiers.
- Keep the output factual and concise.
- Focus on the customer's problem, the observed signals, and the current status.
- Return JSON with exactly these keys: summary, problem_statement, facts, source_signals.

Customer ID: {demo_payload["customer_id"]}
Journey stage: {journey["journey_stage"]}
Risk label: {journey["risk_label"]}
Friction points: {", ".join(journey["friction_points"])}
Preferred channel: {profile["preferred_channel"]}
Recent issue: {profile["recent_issue"]}
Recommended action: {recommendation["recommended_action"]}
Rationale: {recommendation["rationale"]}
Source channels seen: {", ".join(source_signals)}
Evidence lines:
{chr(10).join(f"- {item}" for item in evidence)}
Audit steps:
{chr(10).join(f"- {step}" for step in audit_steps)}

Desired JSON shape:
{{
  "summary": "one short sentence",
  "problem_statement": "one short sentence",
  "facts": ["fact 1", "fact 2", "fact 3"],
  "source_signals": ["web", "app", "support"]
}}
""".strip()


def _parse_fact_response(content: str) -> dict[str, Any] | None:
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    parsed = _try_parse_json(candidate)
    if parsed is None:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = _try_parse_json(candidate[start : end + 1])
    if not isinstance(parsed, dict):
        return None

    summary = str(parsed.get("summary", "")).strip()
    problem_statement = str(parsed.get("problem_statement", "")).strip()
    facts = [str(item).strip() for item in parsed.get("facts", []) if str(item).strip()]
    source_signals = [str(item).strip() for item in parsed.get("source_signals", []) if str(item).strip()]
    if not summary or not problem_statement or not facts:
        return None
    return {
        "summary": summary,
        "problem_statement": problem_statement,
        "facts": facts[:5],
        "source_signals": source_signals[:5],
    }


def _try_parse_json(content: str) -> Any:
    try:
        return json.loads(content)
    except Exception:
        return None


def _build_judge_fallback(demo_payload: dict[str, Any]) -> dict[str, Any]:
    journey = demo_payload.get("journey", {})
    recommendation = demo_payload.get("recommendation", {})
    criteria = {
        "evidence_backed": bool(journey.get("evidence")),
        "privacy_preserved": bool(str(demo_payload.get("customer_id", "")).startswith("CUST-")),
        "governance_explained": bool(demo_payload.get("gates")),
        "audit_traced": bool(demo_payload.get("audit_trail")),
        "decision_clear": bool(journey.get("journey_stage") and recommendation.get("recommended_action")),
    }
    score = sum(20 for passed in criteria.values() if passed)
    return {
        "score": score,
        "passed": score >= 80,
        "summary": "Local safety judge used because the LLM judge was unavailable.",
        "criteria": criteria,
    }


def _build_customer_fact_fallback(demo_payload: dict[str, Any]) -> dict[str, Any]:
    journey = demo_payload["journey"]
    recommendation = demo_payload["recommendation"]
    profile = demo_payload["profile"]
    timeline = demo_payload.get("timeline", [])
    source_signals = sorted({str(event.get("channel", "unknown")) for event in timeline})
    facts = [
        f"The customer is in the {journey['journey_stage']} stage with {journey['risk_label']} risk.",
        f"Observed friction points: {', '.join(journey['friction_points'])}.",
        f"Profile signal: preferred channel is {profile['preferred_channel']} and recent issue is {profile['recent_issue']}.",
        f"Recommended action: {recommendation['recommendation_category']} via {recommendation['recommended_action']}.",
    ]
    return {
        "summary": f"The case shows {journey['risk_label']} risk centered on {', '.join(journey['friction_points'])}.",
        "problem_statement": profile["recent_issue"],
        "facts": facts,
        "source_signals": source_signals,
    }


def _build_customer_profile_prompt(customer: Any, timeline: list[Any], journey: JourneyResult) -> str:
    evidence = journey.evidence
    source_signals = sorted({str(event.channel) for event in timeline})
    return f"""
Convert the merged customer journey into a compact profile.

Rules:
- Do not invent customer preferences.
- Do not include personal data.
- Use only the supplied signals.
- Return JSON with exactly these keys: customer_id, preferred_channel, sentiment, recent_issue, product_interest, loyalty_tier, risk_level.

Customer ID: {customer.customer_id}
Existing profile hints:
- preferred_channel: {customer.preferred_channel}
- loyalty_tier: {customer.loyalty_tier}
- product_interest: {customer.product_family}
Journey stage: {journey.journey_stage}
Risk label: {journey.risk_label}
Friction points: {", ".join(journey.friction_points)}
Evidence:
{chr(10).join(f"- {item}" for item in evidence)}
Source signals: {", ".join(source_signals)}

Desired JSON shape:
{{
  "customer_id": "{customer.customer_id}",
  "preferred_channel": "email",
  "sentiment": "neutral",
  "recent_issue": "billing_issue",
  "product_interest": "premium_plan",
  "loyalty_tier": "silver",
  "risk_level": "high"
}}
""".strip()


def _parse_customer_profile_response(content: str) -> dict[str, Any] | None:
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    parsed = _try_parse_json(candidate)
    if parsed is None:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = _try_parse_json(candidate[start : end + 1])
    if not isinstance(parsed, dict):
        return None

    required = ["customer_id", "preferred_channel", "sentiment", "recent_issue", "product_interest", "loyalty_tier", "risk_level"]
    values = {key: str(parsed.get(key, "")).strip() for key in required}
    if not all(values.values()):
        return None
    return values


def _build_customer_profile_fallback(customer: Any, journey: JourneyResult) -> CustomerProfile:
    return CustomerProfile(
        customer_id=customer.customer_id,
        preferred_channel=customer.preferred_channel,
        sentiment="llm_unavailable",
        recent_issue=", ".join(journey.friction_points) or journey.journey_stage,
        product_interest=customer.product_family,
        loyalty_tier=customer.loyalty_tier,
        risk_level=journey.risk_label,
    )


def _build_recommendation_prompt(
    customer: Any,
    profile: CustomerProfile,
    journey: JourneyResult,
) -> str:
    evidence = journey.evidence
    return f"""
Choose the next best action for this customer.

Rules:
- Use only the supplied evidence.
- Do not invent actions or policy rules.
- Keep the action practical and judge-friendly.
- Return JSON with exactly these keys: customer_id, recommended_action, recommendation_category, rationale, requires_manual_review.

Customer ID: {customer.customer_id}
Journey stage: {journey.journey_stage}
Risk label: {journey.risk_label}
Friction points: {", ".join(journey.friction_points)}
Preferred channel: {profile.preferred_channel}
Sentiment: {profile.sentiment}
Recent issue: {profile.recent_issue}
Evidence:
{chr(10).join(f"- {item}" for item in evidence)}

Desired JSON shape:
{{
  "customer_id": "{customer.customer_id}",
  "recommended_action": "Send a personalized recovery message in the preferred channel.",
  "recommendation_category": "onboarding_recovery",
  "rationale": "The customer has onboarding friction and needs a guided next step.",
  "requires_manual_review": false
}}
""".strip()


def _parse_recommendation_response(content: str) -> dict[str, Any] | None:
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    parsed = _try_parse_json(candidate)
    if parsed is None:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = _try_parse_json(candidate[start : end + 1])
    if not isinstance(parsed, dict):
        return None

    required = ["customer_id", "recommended_action", "recommendation_category", "rationale", "requires_manual_review"]
    customer_id = str(parsed.get("customer_id", "")).strip()
    action = str(parsed.get("recommended_action", "")).strip()
    category = str(parsed.get("recommendation_category", "")).strip()
    rationale = str(parsed.get("rationale", "")).strip()
    requires_manual_review = bool(parsed.get("requires_manual_review", False))
    if not customer_id or not action or not category or not rationale:
        return None
    return {
        "customer_id": customer_id,
        "recommended_action": action,
        "recommendation_category": category,
        "rationale": rationale,
        "requires_manual_review": requires_manual_review,
    }


def _build_recommendation_fallback(customer: Any, profile: CustomerProfile, journey: JourneyResult) -> RecommendationResult:
    return RecommendationResult(
        customer_id=customer.customer_id,
        recommended_action="Route the case to a CX operator for manual review because LLM action selection is unavailable.",
        recommendation_category="manual_review",
        rationale=f"The system has evidence for {journey.journey_stage} with {profile.risk_level} risk, but no LLM recommendation was produced.",
        requires_manual_review=True,
    )


def _build_unified_journey_prompt(demo_payload: dict[str, Any]) -> str:
    timeline = demo_payload.get("timeline", [])
    facts = demo_payload.get("customer_facts") or {}
    journey = demo_payload["journey"]
    touchpoints = [
        f"- {event.get('timestamp', '')} | {event.get('channel', 'unknown')} | {event.get('event_type', 'unknown')} | {event.get('outcome', 'unknown')}"
        for event in timeline
    ]
    source_signals = sorted({str(event.get("channel", "unknown")) for event in timeline})
    return f"""
Merge these customer touchpoints into one short unified view.

Rules:
- Do not quote raw messages.
- Do not include personal data.
- Keep it concise and judge-friendly.
- Focus on what happened, where friction appeared, and what the customer is trying to do.
- Return JSON with exactly these keys: summary, key_touchpoints, source_signals.

Customer ID: {demo_payload["customer_id"]}
Journey stage: {journey["journey_stage"]}
Risk label: {journey["risk_label"]}
Problem statement: {facts.get("problem_statement", "unknown")}
Source signals: {", ".join(source_signals)}
Touchpoints:
{chr(10).join(touchpoints)}

Desired JSON shape:
{{
  "summary": "one short sentence",
  "key_touchpoints": ["touchpoint 1", "touchpoint 2", "touchpoint 3"],
  "source_signals": ["web", "app", "support"]
}}
""".strip()


def _parse_unified_journey_response(content: str) -> dict[str, Any] | None:
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    parsed = _try_parse_json(candidate)
    if parsed is None:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = _try_parse_json(candidate[start : end + 1])
    if not isinstance(parsed, dict):
        return None
    summary = str(parsed.get("summary", "")).strip()
    key_touchpoints = [str(item).strip() for item in parsed.get("key_touchpoints", []) if str(item).strip()]
    source_signals = [str(item).strip() for item in parsed.get("source_signals", []) if str(item).strip()]
    if not summary or not key_touchpoints:
        return None
    return {
        "summary": summary,
        "key_touchpoints": key_touchpoints[:5],
        "source_signals": source_signals[:5],
    }


def _build_unified_journey_fallback(demo_payload: dict[str, Any]) -> dict[str, Any]:
    timeline = demo_payload.get("timeline", [])
    journey = demo_payload["journey"]
    key_touchpoints = [
        f"{event.get('timestamp', '')} | {event.get('channel', 'unknown')} | {event.get('event_type', 'unknown')} | {event.get('outcome', 'unknown')}"
        for event in timeline[:5]
    ]
    source_signals = sorted({str(event.get("channel", "unknown")) for event in timeline})
    return {
        "summary": f"Unified journey for {demo_payload['customer_id']} is in {journey['journey_stage']} with {journey['risk_label']} risk.",
        "key_touchpoints": key_touchpoints,
        "source_signals": source_signals,
    }


def _build_source_bucket_prompt(event_payload: dict[str, Any]) -> str:
    metadata = event_payload.get("metadata", {})
    return f"""
Classify this event into one source bucket.

Event channel: {event_payload.get("channel", "unknown")}
Event type: {event_payload.get("event_type", "unknown")}
Stage hint: {event_payload.get("stage_hint", "unknown")}
Outcome: {event_payload.get("outcome", "unknown")}
Metadata: {json.dumps(metadata, ensure_ascii=False)}

Return JSON in this exact shape:
{{"source_bucket":"web"}}
""".strip()


def _parse_source_bucket_response(content: str) -> str | None:
    candidate = content.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    parsed = _try_parse_json(candidate)
    if not isinstance(parsed, dict):
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = _try_parse_json(candidate[start : end + 1])
    if not isinstance(parsed, dict):
        return None
    bucket = str(parsed.get("source_bucket", "")).strip().lower()
    return bucket or None


def _fallback_source_bucket(channel: str) -> str:
    normalized = channel.lower()
    bucket_aliases = {
        "payment": "payments",
        "transaction": "payments",
        "email": "communications",
        "communication": "communications",
        "survey": "surveys",
    }
    return bucket_aliases.get(normalized, normalized)

from __future__ import annotations

from cx_agent.models import JourneyResult, RecommendationResult


def evaluate_case(
    expected_stage: str,
    expected_friction: str,
    expected_category: str,
    journey: JourneyResult,
    recommendation: RecommendationResult,
) -> dict[str, bool]:
    return {
        "journey_stage": journey.journey_stage == expected_stage,
        "friction_label": expected_friction in journey.friction_points,
        "recommendation_category": recommendation.recommendation_category == expected_category,
    }


def summarize_scores(results: list[dict[str, bool]]) -> dict[str, float]:
    total_checks = sum(len(result) for result in results)
    passed_checks = sum(1 for result in results for passed in result.values() if passed)
    pass_rate = passed_checks / total_checks if total_checks else 0.0
    return {
        "total_cases": float(len(results)),
        "total_checks": float(total_checks),
        "passed_checks": float(passed_checks),
        "pass_rate": pass_rate,
    }


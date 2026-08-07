from __future__ import annotations

from cx_agent.llm.openrouter import generate_judge_assessment
from cx_agent.models import JudgeResult
from cx_agent.settings import Settings


def judge_demo_output(settings: Settings, demo_payload: dict[str, object]) -> JudgeResult:
    return generate_judge_assessment(settings, demo_payload)


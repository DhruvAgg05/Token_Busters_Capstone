from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_name: str
    log_level: str
    mask_pii: bool
    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_model: str
    openrouter_app_name: str
    openrouter_site_url: str
    openrouter_timeout_seconds: float
    default_actor_role: str
    default_region: str
    default_data_dir: Path
    default_output_dir: Path
    enable_llm: bool
    enable_synthetic_data: bool
    pii_salt: str
    enable_ownership_gate: bool
    enable_capability_gate: bool
    require_evidence_for_recommendations: bool
    enable_eval_gate: bool
    min_eval_pass_rate: float


def load_settings(project_root: Path | None = None) -> Settings:
    root = project_root or Path(__file__).resolve().parents[2]
    _load_dotenv(root / ".env")

    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        app_name=os.getenv("APP_NAME", "cx-agent"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        mask_pii=_parse_bool(os.getenv("MASK_PII"), True),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        openrouter_app_name=os.getenv("OPENROUTER_APP_NAME", "TokenBusters-CX-Agent"),
        openrouter_site_url=os.getenv("OPENROUTER_SITE_URL", "http://localhost"),
        openrouter_timeout_seconds=float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "30")),
        default_actor_role=os.getenv("DEFAULT_ACTOR_ROLE", "support_lead"),
        default_region=os.getenv("DEFAULT_REGION", "IN"),
        default_data_dir=root / os.getenv("DEFAULT_DATA_DIR", "data"),
        default_output_dir=root / os.getenv("DEFAULT_OUTPUT_DIR", "data/processed"),
        enable_llm=_parse_bool(os.getenv("ENABLE_LLM"), True),
        enable_synthetic_data=_parse_bool(os.getenv("ENABLE_SYNTHETIC_DATA"), True),
        pii_salt=os.getenv("PII_SALT", ""),
        enable_ownership_gate=_parse_bool(os.getenv("ENABLE_OWNERSHIP_GATE"), True),
        enable_capability_gate=_parse_bool(os.getenv("ENABLE_CAPABILITY_GATE"), True),
        require_evidence_for_recommendations=_parse_bool(
            os.getenv("REQUIRE_EVIDENCE_FOR_RECOMMENDATIONS"), True
        ),
        enable_eval_gate=_parse_bool(os.getenv("ENABLE_EVAL_GATE"), True),
        min_eval_pass_rate=float(os.getenv("MIN_EVAL_PASS_RATE", "0.80")),
    )

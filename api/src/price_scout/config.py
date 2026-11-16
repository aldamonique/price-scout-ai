from pathlib import Path
from typing import Literal

from openai.types.shared.reasoning_effort import ReasoningEffort
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class ModelSettings(BaseModel):
    model: str
    reasoning_effort: ReasoningEffort | None = None
    input_usd_per_mtok: float | None = None
    output_usd_per_mtok: float | None = None
    prompt_version: str


class LakeSettings(BaseModel):
    backend: Literal["local", "s3"] = "local"
    bucket: str = "price-scout-lake"
    endpoint: str | None = None
    region: str = "us-east-1"
    use_ssl: bool = True
    access_key_id: str | None = None
    secret_access_key: str | None = None
    mirror_dir: Path | None = None

    @property
    def endpoint_url(self) -> str | None:
        if self.endpoint is None:
            return None
        return f"{'https' if self.use_ssl else 'http'}://{self.endpoint}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_nested_delimiter="__",
        env_parse_none_str="null",
        extra="ignore",
    )

    serpapi_key: str
    openai_api_key: str

    agent: ModelSettings
    judge: ModelSettings

    agent_workers: int = 2
    max_requests_per_hour: int | None = 30
    admin_token: str | None = None
    lake: LakeSettings = LakeSettings()
    data_dir: Path = REPO_ROOT / "data"
    analytics_dir: Path = REPO_ROOT / "analytics"
    eval_results_dir: Path = REPO_ROOT / "api" / "evals" / "results"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

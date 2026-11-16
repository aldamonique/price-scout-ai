import pytest
from pydantic import ValidationError

from price_scout.config import Settings

REQUIRED = {
    "SERPAPI_KEY": "serp",
    "OPENAI_API_KEY": "sk-test",
    "AGENT__MODEL": "agent-model",
    "JUDGE__MODEL": "judge-model",
    "AGENT__PROMPT_VERSION": "v3",
    "JUDGE__PROMPT_VERSION": "v1",
}


def set_env(monkeypatch: pytest.MonkeyPatch, values: dict[str, str]) -> None:
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_each_task_reads_its_own_model_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_env(
        monkeypatch,
        {**REQUIRED, "AGENT__REASONING_EFFORT": "medium", "JUDGE__INPUT_USD_PER_MTOK": "1.5"},
    )

    settings = Settings(_env_file=None)

    assert (settings.agent.model, settings.judge.model) == ("agent-model", "judge-model")
    assert settings.agent.reasoning_effort == "medium"
    assert settings.judge.input_usd_per_mtok == 1.5


def test_each_task_reads_its_prompt_version(monkeypatch: pytest.MonkeyPatch) -> None:
    set_env(monkeypatch, REQUIRED)

    settings = Settings(_env_file=None)

    assert (settings.agent.prompt_version, settings.judge.prompt_version) == ("v3", "v1")
    assert settings.agent_workers == 2


def test_null_turns_reasoning_off(monkeypatch: pytest.MonkeyPatch) -> None:
    set_env(monkeypatch, {**REQUIRED, "JUDGE__REASONING_EFFORT": "null"})

    settings = Settings(_env_file=None)

    assert settings.judge.reasoning_effort is None


def test_a_missing_model_stops_the_app_and_names_it(monkeypatch: pytest.MonkeyPatch) -> None:
    set_env(monkeypatch, {k: v for k, v in REQUIRED.items() if k != "JUDGE__MODEL"})
    monkeypatch.delenv("JUDGE__MODEL", raising=False)

    with pytest.raises(ValidationError, match=r"judge"):
        Settings(_env_file=None)


def test_a_missing_prompt_version_stops_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    set_env(monkeypatch, {k: v for k, v in REQUIRED.items() if k != "AGENT__PROMPT_VERSION"})
    monkeypatch.delenv("AGENT__PROMPT_VERSION", raising=False)

    with pytest.raises(ValidationError, match=r"agent"):
        Settings(_env_file=None)


def test_the_lake_is_local_unless_the_environment_says_s3(monkeypatch: pytest.MonkeyPatch) -> None:
    set_env(monkeypatch, REQUIRED)
    assert Settings(_env_file=None).lake.backend == "local"

    set_env(
        monkeypatch,
        {"LAKE__BACKEND": "s3", "LAKE__ENDPOINT": "localhost:9000", "LAKE__USE_SSL": "false"},
    )
    lake = Settings(_env_file=None).lake

    assert (lake.backend, lake.endpoint_url) == ("s3", "http://localhost:9000")

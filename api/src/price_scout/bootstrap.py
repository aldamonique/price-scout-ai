import logging
from collections.abc import Callable

import boto3
import httpx
import openai
from fastapi import FastAPI
from openai.types.shared.reasoning_effort import ReasoningEffort
from openai.types.shared_params import Reasoning

from price_scout.application.observability.get_eval_runs import GetEvalRuns
from price_scout.application.observability.get_overview import GetObservability
from price_scout.application.observability.get_request_calls import GetRequestCalls
from price_scout.application.search.search_offers import SearchOffers
from price_scout.application.shopping_request.delete_request import DeleteShoppingRequest
from price_scout.application.shopping_request.get_request import GetShoppingRequest
from price_scout.application.shopping_request.list_requests import ListShoppingRequests
from price_scout.application.shopping_request.resume_requests import ResumeShoppingRequests
from price_scout.application.shopping_request.run_request import RunShoppingRequest
from price_scout.application.shopping_request.step_log import StepLog
from price_scout.application.shopping_request.submit_request import SubmitShoppingRequest
from price_scout.application.shopping_request.toolbox import AgentToolbox
from price_scout.config import ModelSettings, Settings
from price_scout.domain.catalog.ports import RawStore
from price_scout.domain.shopping_request.models import ShoppingRequest
from price_scout.infrastructure.context import load_business_context, load_store_policies
from price_scout.infrastructure.duckdb.call_log import DuckDbCallLog
from price_scout.infrastructure.duckdb.catalog import DuckDbCatalog
from price_scout.infrastructure.duckdb.connection import open_warehouse
from price_scout.infrastructure.duckdb.judgment_repository import DuckDbJudgmentRepository
from price_scout.infrastructure.duckdb.medallion import MedallionSql
from price_scout.infrastructure.duckdb.observability import DuckDbObservability
from price_scout.infrastructure.duckdb.shopping_request_repository import (
    DuckDbShoppingRequestRepository,
)
from price_scout.infrastructure.evals.json_results import JsonEvalResults
from price_scout.infrastructure.jobs.thread_pool import ThreadPoolJobRunner
from price_scout.infrastructure.lake.cached_source import CachedOfferSource
from price_scout.infrastructure.lake.mirrored_store import MirroredRawStore
from price_scout.infrastructure.lake.raw_store import FileRawStore
from price_scout.infrastructure.lake.s3_raw_store import S3RawStore
from price_scout.infrastructure.llm.offer_judge import LlmOfferJudge
from price_scout.infrastructure.llm.shopping_agent import OpenAiShoppingAgent
from price_scout.infrastructure.llm.structured import OpenAiStructuredLlm
from price_scout.infrastructure.llm.tracing import CallTracer, ObservedLlm
from price_scout.infrastructure.llm.usage import ModelPricing
from price_scout.infrastructure.serpapi.client import SerpApiOfferSource
from price_scout.presentation.app import UseCases, create_app

logger = logging.getLogger(__name__)


def new_raw_store(settings: Settings) -> RawStore:
    lake = settings.lake
    if lake.backend == "local":
        return FileRawStore(settings.data_dir / "bronze")
    client = boto3.client(
        "s3",
        endpoint_url=lake.endpoint_url,
        region_name=lake.region,
        aws_access_key_id=lake.access_key_id,
        aws_secret_access_key=lake.secret_access_key,
    )
    lake_store = S3RawStore(client, lake.bucket)
    if lake.mirror_dir is None:
        return lake_store
    return MirroredRawStore(lake_store, FileRawStore(lake.mirror_dir))


def bronze_file_for(settings: Settings) -> Callable[[str], str]:
    lake = settings.lake
    if lake.backend == "local":
        bronze_dir = (settings.data_dir / "bronze").as_posix()
        return lambda search_id: f"{bronze_dir}/{search_id}.json"
    return lambda search_id: f"s3://{lake.bucket}/bronze/{search_id}.json"


def build_app(settings: Settings) -> FastAPI:
    configure_logging(settings.log_level)

    connection = open_warehouse(settings.data_dir, settings.lake)
    requests = DuckDbShoppingRequestRepository(connection)

    llm_client = openai.OpenAI(api_key=settings.openai_api_key)
    business_context = load_business_context()
    catalog = DuckDbCatalog(
        connection, MedallionSql(settings.analytics_dir), bronze_file_for(settings)
    )
    raw_store = new_raw_store(settings)
    call_log = DuckDbCallLog(connection)
    tracer = CallTracer(call_log)

    search_offers = SearchOffers(
        offer_source=CachedOfferSource(
            inner=SerpApiOfferSource(settings.serpapi_key, httpx.Client()),
            store=raw_store,
        ),
        raw_store=raw_store,
        offer_judge=LlmOfferJudge(
            ObservedLlm(
                OpenAiStructuredLlm(
                    llm_client, settings.judge.model, reasoning(settings.judge.reasoning_effort)
                ),
                tracer,
                task="judge",
                model=settings.judge.model,
                prompt_version=settings.judge.prompt_version,
                pricing=pricing(settings.judge),
            ),
            business_context=business_context,
            prompt_version=settings.judge.prompt_version,
            model=settings.judge.model,
        ),
        judgments=DuckDbJudgmentRepository(connection),
        catalog=catalog,
        store_policies=load_store_policies(),
    )

    def new_toolbox(step_log: StepLog, request: ShoppingRequest) -> AgentToolbox:
        return AgentToolbox(search_offers, catalog, step_log, request.market, request.budget)

    agent = OpenAiShoppingAgent(
        llm_client,
        settings.agent.model,
        reasoning(settings.agent.reasoning_effort),
        business_context,
        pricing(settings.agent),
        prompt_version=settings.agent.prompt_version,
        tracer=tracer,
    )
    runner = ThreadPoolJobRunner(max_workers=settings.agent_workers)

    run_request = RunShoppingRequest(agent, new_toolbox, requests)
    resumed = ResumeShoppingRequests(requests, runner, run_request).execute()
    if resumed:
        logger.info("resumed %d unfinished shopping requests", resumed)

    use_cases = UseCases(
        submit_request=SubmitShoppingRequest(
            requests, runner, run_request, max_per_hour=settings.max_requests_per_hour
        ),
        get_request=GetShoppingRequest(requests),
        list_requests=ListShoppingRequests(requests),
        get_observability=GetObservability(DuckDbObservability(connection)),
        get_request_calls=GetRequestCalls(requests, call_log),
        delete_request=DeleteShoppingRequest(requests, call_log),
        get_eval_runs=GetEvalRuns(JsonEvalResults(settings.eval_results_dir)),
    )
    return create_app(use_cases, on_shutdown=runner.shutdown, admin_token=settings.admin_token)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpcore", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def reasoning(effort: ReasoningEffort | None) -> Reasoning | None:
    return None if effort is None else {"effort": effort}


def pricing(model: ModelSettings) -> ModelPricing | None:
    if model.input_usd_per_mtok is None or model.output_usd_per_mtok is None:
        return None
    return ModelPricing(model.input_usd_per_mtok, model.output_usd_per_mtok)

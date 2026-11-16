from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import ANY, Stubber

from price_scout.config import LakeSettings
from price_scout.domain.catalog.models import RawSearch
from price_scout.infrastructure.lake.mirrored_store import MirroredRawStore
from price_scout.infrastructure.lake.raw_store import FileRawStore
from price_scout.infrastructure.lake.s3_raw_store import S3RawStore

RAW = RawSearch(
    search_id="abc",
    query="sofá",
    country="br",
    fetched_at=datetime(2026, 11, 15, 12, 0, tzinfo=UTC),
    payload={"shopping_results": []},
)
KEY = {"Bucket": "lake", "Key": "bronze/abc.json"}


@pytest.fixture
def s3() -> tuple[S3RawStore, Stubber]:
    client = boto3.client(
        "s3", region_name="us-east-1", aws_access_key_id="k", aws_secret_access_key="s"
    )
    return S3RawStore(client, "lake"), Stubber(client)


def test_s3_writes_a_new_search_under_bronze(s3: tuple[S3RawStore, Stubber]) -> None:
    store, stub = s3
    stub.add_client_error("head_object", "404", expected_params=KEY)
    stub.add_response(
        "put_object",
        {},
        {**KEY, "Body": ANY, "ContentType": "application/json"},
    )

    with stub:
        store.save(RAW)

    stub.assert_no_pending_responses()


def test_s3_never_rewrites_a_search(s3: tuple[S3RawStore, Stubber]) -> None:
    store, stub = s3
    stub.add_response("head_object", {}, KEY)

    with stub:
        store.save(RAW)

    stub.assert_no_pending_responses()


def test_s3_reads_back_what_was_written(s3: tuple[S3RawStore, Stubber]) -> None:
    store, stub = s3
    body = RAW.model_dump_json().encode()
    stub.add_response("get_object", {"Body": StreamingBody(BytesIO(body), len(body))}, KEY)

    with stub:
        assert store.load("abc") == RAW


def test_s3_returns_none_for_a_missing_search(s3: tuple[S3RawStore, Stubber]) -> None:
    store, stub = s3
    stub.add_client_error("get_object", "NoSuchKey", expected_params=KEY)

    with stub:
        assert store.load("abc") is None


def test_s3_access_errors_are_not_hidden(s3: tuple[S3RawStore, Stubber]) -> None:
    store, stub = s3
    stub.add_client_error("get_object", "AccessDenied", http_status_code=403)

    with stub, pytest.raises(Exception, match="AccessDenied"):
        store.load("abc")


def test_the_local_store_has_the_same_contract(tmp_path: Path) -> None:
    store = FileRawStore(tmp_path)

    assert store.load("abc") is None
    store.save(RAW)
    store.save(RAW.model_copy(update={"country": "us"}))

    assert store.load("abc") == RAW


def test_minio_endpoints_get_a_scheme_and_aws_gets_none() -> None:
    minio = LakeSettings(backend="s3", endpoint="localhost:9000", use_ssl=False)

    assert minio.endpoint_url == "http://localhost:9000"
    assert LakeSettings(backend="s3").endpoint_url is None


def test_the_mirror_keeps_a_copy_of_every_search(tmp_path: Path) -> None:
    lake, disk = FileRawStore(tmp_path / "lake"), FileRawStore(tmp_path / "disk")

    MirroredRawStore(lake, disk).save(RAW)

    assert lake.load("abc") == RAW
    assert disk.load("abc") == RAW


def test_a_lost_lake_is_refilled_from_the_mirror(tmp_path: Path) -> None:
    disk = FileRawStore(tmp_path / "disk")
    disk.save(RAW)
    empty_lake = FileRawStore(tmp_path / "new-lake")

    assert MirroredRawStore(empty_lake, disk).load("abc") == RAW
    assert empty_lake.load("abc") == RAW


def test_a_search_missing_everywhere_is_none(tmp_path: Path) -> None:
    store = MirroredRawStore(FileRawStore(tmp_path / "a"), FileRawStore(tmp_path / "b"))

    assert store.load("abc") is None

from typing import TYPE_CHECKING

from botocore.exceptions import ClientError

from price_scout.domain.catalog.models import RawSearch

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

NOT_FOUND = {"404", "NoSuchKey", "NotFound"}


class S3RawStore:
    def __init__(self, client: "S3Client", bucket: str, prefix: str = "bronze/") -> None:
        self._client = client
        self._bucket = bucket
        self._prefix = prefix

    def save(self, raw: RawSearch) -> None:
        key = self._key(raw.search_id)
        if self._exists(key):
            return
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=raw.model_dump_json().encode("utf-8"),
            ContentType="application/json",
        )

    def load(self, search_id: str) -> RawSearch | None:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=self._key(search_id))
        except ClientError as error:
            if _code(error) in NOT_FOUND:
                return None
            raise
        return RawSearch.model_validate_json(response["Body"].read())

    def _exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
        except ClientError as error:
            if _code(error) in NOT_FOUND:
                return False
            raise
        return True

    def _key(self, search_id: str) -> str:
        return f"{self._prefix}{search_id}.json"


def _code(error: ClientError) -> str:
    return str(error.response.get("Error", {}).get("Code", ""))

import json
from typing import Any

import httpx2
import openai

type Reply = dict[str, Any]


def tool_call(name: str, arguments: dict[str, Any], call_id: str) -> Reply:
    return {
        "type": "function_call",
        "id": f"fc_{call_id}",
        "call_id": call_id,
        "name": name,
        "arguments": json.dumps(arguments),
        "status": "completed",
    }


def message(payload: dict[str, Any]) -> Reply:
    return {
        "type": "message",
        "id": "msg_final",
        "role": "assistant",
        "status": "completed",
        "content": [{"type": "output_text", "text": json.dumps(payload), "annotations": []}],
    }


class FakeResponsesApi:
    def __init__(self, outputs: list[list[Reply]], status: str = "completed") -> None:
        self._outputs = iter(outputs)
        self._status = status
        self.requests: list[dict[str, Any]] = []

    def client(self) -> openai.OpenAI:
        return openai.OpenAI(
            api_key="test", http_client=httpx2.Client(transport=httpx2.MockTransport(self._handle))
        )

    def _handle(self, request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content)
        self.requests.append(body)
        number = len(self.requests)
        return httpx2.Response(
            200,
            json={
                "id": f"resp_{number}",
                "object": "response",
                "created_at": 0,
                "status": self._status,
                "model": body["model"],
                "output": next(self._outputs),
                "parallel_tool_calls": True,
                "tool_choice": "auto",
                "tools": [],
                "usage": {
                    "input_tokens": 1000,
                    "output_tokens": 200,
                    "total_tokens": 1200,
                    "input_tokens_details": {"cached_tokens": 0},
                    "output_tokens_details": {"reasoning_tokens": 0},
                },
            },
        )


def failing_client() -> openai.OpenAI:
    def handler(_: httpx2.Request) -> httpx2.Response:
        error = {"message": "bad key", "type": "invalid_request_error"}
        return httpx2.Response(401, json={"error": error})

    return openai.OpenAI(
        api_key="test",
        max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )

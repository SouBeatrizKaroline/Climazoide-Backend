import httpx

from app.services.live_data import _fetch_json


async def test_public_json_source_retries_transient_status_errors() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503, request=request)
        return httpx.Response(200, json={"status": "available"}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        payload = await _fetch_json(client, "https://example.test/data", {})

    assert payload == {"status": "available"}
    assert attempts == 3

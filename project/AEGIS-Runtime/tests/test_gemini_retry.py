import time
from unittest.mock import MagicMock

from google.genai import errors as genai_errors

from backend.config.config import generate_content_with_retry, _extract_retry_delay


def _make_api_error(code, status, details=None):
    error = genai_errors.APIError.__new__(genai_errors.APIError)
    error.code = code
    error.status = status
    error.details = details
    error.message = status
    return error


def test_succeeds_immediately_when_no_error():
    client = MagicMock()
    client.models.generate_content.return_value = "ok"

    result = generate_content_with_retry(client, model="gemini-2.5-flash", contents="hi")

    assert result == "ok"
    assert client.models.generate_content.call_count == 1


def test_retries_on_rate_limit_then_succeeds(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    client = MagicMock()
    rate_limit_error = _make_api_error(429, "RESOURCE_EXHAUSTED")
    client.models.generate_content.side_effect = [rate_limit_error, "ok"]

    result = generate_content_with_retry(
        client, max_retries=3, model="gemini-2.5-flash", contents="hi"
    )

    assert result == "ok"
    assert client.models.generate_content.call_count == 2


def test_retries_on_server_error_then_succeeds(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    client = MagicMock()
    server_error = _make_api_error(503, "UNAVAILABLE")
    client.models.generate_content.side_effect = [server_error, "ok"]

    result = generate_content_with_retry(
        client, max_retries=3, model="gemini-2.5-flash", contents="hi"
    )

    assert result == "ok"
    assert client.models.generate_content.call_count == 2


def test_does_not_retry_non_transient_errors():
    client = MagicMock()
    bad_request = _make_api_error(400, "INVALID_ARGUMENT")
    client.models.generate_content.side_effect = bad_request

    try:
        generate_content_with_retry(client, max_retries=3, model="gemini-2.5-flash", contents="hi")
        assert False, "expected the non-transient error to propagate immediately"
    except genai_errors.APIError:
        pass

    # Must NOT have retried -- only one call for a genuinely bad request.
    assert client.models.generate_content.call_count == 1


def test_raises_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    client = MagicMock()
    rate_limit_error = _make_api_error(429, "RESOURCE_EXHAUSTED")
    client.models.generate_content.side_effect = rate_limit_error

    try:
        generate_content_with_retry(client, max_retries=2, model="gemini-2.5-flash", contents="hi")
        assert False, "expected the error to propagate after exhausting retries"
    except genai_errors.APIError:
        pass

    # Initial attempt + 2 retries = 3 total calls.
    assert client.models.generate_content.call_count == 3


def test_honors_server_suggested_retry_delay(monkeypatch):
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda seconds: sleep_calls.append(seconds))

    client = MagicMock()
    rate_limit_error = _make_api_error(
        429,
        "RESOURCE_EXHAUSTED",
        details={
            "error": {
                "code": 429,
                "status": "RESOURCE_EXHAUSTED",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.RetryInfo",
                        "retryDelay": "11s",
                    }
                ],
            }
        },
    )
    client.models.generate_content.side_effect = [rate_limit_error, "ok"]

    generate_content_with_retry(client, max_retries=3, model="gemini-2.5-flash", contents="hi")

    assert sleep_calls == [11.0]


def test_honors_retry_delay_from_real_apierror_construction(monkeypatch):
    """
    Builds the error the same way google-genai actually does --
    via APIError(code, response_json) -- rather than a hand-rolled
    mock, so this test would have caught the real nested-structure
    mismatch that the hand-rolled version above missed.
    """
    from google.genai import errors as genai_errors

    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda seconds: sleep_calls.append(seconds))

    response_json = {
        "error": {
            "code": 429,
            "message": "You exceeded your current quota...",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.RetryInfo",
                    "retryDelay": "11s",
                }
            ],
        }
    }
    real_error = genai_errors.APIError(429, response_json)

    client = MagicMock()
    client.models.generate_content.side_effect = [real_error, "ok"]

    result = generate_content_with_retry(
        client, max_retries=3, model="gemini-2.5-flash", contents="hi"
    )

    assert result == "ok"
    assert sleep_calls == [11.0]


def test_extract_retry_delay_parses_seconds_string():
    error = _make_api_error(
        429,
        "RESOURCE_EXHAUSTED",
        details={"error": {"details": [{"retryDelay": "3.5s"}]}},
    )
    assert _extract_retry_delay(error) == 3.5


def test_extract_retry_delay_returns_none_when_absent():
    error = _make_api_error(429, "RESOURCE_EXHAUSTED", details=None)
    assert _extract_retry_delay(error) is None


if __name__ == "__main__":
    test_succeeds_immediately_when_no_error()
    test_retries_on_rate_limit_then_succeeds()
    test_retries_on_server_error_then_succeeds()
    test_does_not_retry_non_transient_errors()
    test_raises_after_exhausting_retries()
    test_honors_server_suggested_retry_delay()
    test_honors_retry_delay_from_real_apierror_construction()
    test_extract_retry_delay_parses_seconds_string()
    test_extract_retry_delay_returns_none_when_absent()
    print("All Gemini retry tests passed!")

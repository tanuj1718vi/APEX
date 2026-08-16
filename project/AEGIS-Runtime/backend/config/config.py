import os
import re
import time
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

# Load AEGIS-Runtime/.env explicitly, relative to this file's own
# location -- not relative to the process's current working
# directory. load_dotenv() with no arguments only searches *upward*
# from the CWD, so if the app is started from a parent folder (e.g.
# "project/", so the "apex" and "backend" packages both import
# correctly), it would never find a .env file sitting in this
# subfolder, no matter how correctly the key was set.
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Add it to the .env file."
        )

    return genai.Client(api_key=api_key)


_RETRY_DELAY_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*s")


def _extract_retry_delay(error: "genai_errors.APIError") -> Optional[float]:
    """
    Gemini's 429 responses include a suggested retryDelay (e.g. '11s')
    telling us exactly how long the current quota window has left.
    Honor it when present instead of guessing.

    error.details holds the raw response body, which nests the
    actual list of detail objects at details['error']['details'] --
    but is defensive about other shapes too, since the exact
    structure isn't part of any stable public contract.
    """
    details = getattr(error, "details", None)
    if not details:
        return None

    candidates = []

    if isinstance(details, dict):
        nested = details.get("error", {})
        if isinstance(nested, dict) and isinstance(nested.get("details"), list):
            candidates.extend(nested["details"])
        if isinstance(details.get("details"), list):
            candidates.extend(details["details"])
        candidates.append(details)
    elif isinstance(details, list):
        candidates.extend(details)

    for entry in candidates:
        if not isinstance(entry, dict):
            continue
        retry_delay = entry.get("retryDelay")
        if isinstance(retry_delay, str):
            match = _RETRY_DELAY_PATTERN.search(retry_delay)
            if match:
                return float(match.group(1))

    return None


def generate_content_with_retry(
    client: Any,
    max_retries: int = 3,
    base_delay: float = 2.0,
    **kwargs: Any,
):
    """
    Calls client.models.generate_content(**kwargs), automatically
    retrying with backoff on transient failures:

      - 429 RESOURCE_EXHAUSTED (rate limit / quota) -- honors the
        server's suggested retryDelay when present, otherwise
        exponential backoff.
      - 5xx server errors -- exponential backoff.

    Any other error (invalid API key, malformed request, etc.) is
    raised immediately on the first attempt -- only genuinely
    transient, retryable failures are retried, so a real
    misconfiguration still fails fast and visibly instead of being
    masked by three silent retries.
    """
    last_error: Optional[BaseException] = None

    for attempt in range(max_retries + 1):
        try:
            return client.models.generate_content(**kwargs)
        except genai_errors.APIError as error:
            last_error = error

            is_rate_limited = (
                error.code == 429 or error.status == "RESOURCE_EXHAUSTED"
            )
            is_server_error = (
                error.code is not None and 500 <= error.code < 600
            )

            if not (is_rate_limited or is_server_error):
                raise

            if attempt == max_retries:
                raise

            delay = _extract_retry_delay(error)
            if delay is None:
                delay = base_delay * (2**attempt)

            print(
                f"[Gemini] {error.status or error.code}: retrying in "
                f"{delay:.1f}s (attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(delay)

    # Unreachable in practice (the loop always returns or raises),
    # but keeps type checkers and linters happy.
    if last_error is not None:
        raise last_error
    raise RuntimeError("generate_content_with_retry exhausted retries.")

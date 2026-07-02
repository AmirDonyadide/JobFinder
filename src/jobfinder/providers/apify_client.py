"""Low-level Apify actor execution helpers."""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import MutableMapping
from typing import Any

import requests

from jobfinder.scraper.settings import (
    TOKEN_PLACEHOLDER,
    ApifyTokenSelection,
    ScraperSettings,
)

APIFY_POLL_INTERVAL_SECONDS = 15
APIFY_TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}
RETRYABLE_APIFY_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}
MAX_APIFY_RETRY_DELAY_SECONDS = 300
APIFY_CREDIT_ERROR_TERMS = (
    "not enough credit",
    "no credit",
    "no credits",
    "out of credit",
    "out of credits",
    "credits exhausted",
    "credit balance",
    "not enough funds",
    "insufficient credit",
    "insufficient funds",
    "insufficient balance",
    "account balance",
    "payment required",
    "billing",
    "prepaid",
    "usage limit",
    "out of funds",
    "add a payment method",
)

LOGGER = logging.getLogger("jobfinder.scraper")
SENSITIVE_LOG_KEY_RE = re.compile(
    r"token|authorization|cookie|password|secret|api[_-]?key",
    re.IGNORECASE,
)
SENSITIVE_QUERY_RE = re.compile(
    r"(?i)(token|api[_-]?key|authorization)=([^&\s\"']+)",
)


def redact_for_log(value: Any, *, key: str = "") -> Any:
    """Return a recursively redacted value suitable for diagnostic logging."""
    if key and SENSITIVE_LOG_KEY_RE.search(key):
        return "<redacted>"
    if isinstance(value, dict):
        return {
            str(child_key): redact_for_log(child_value, key=str(child_key))
            for child_key, child_value in value.items()
        }
    if isinstance(value, list):
        return [redact_for_log(item) for item in value]
    if isinstance(value, tuple):
        return [redact_for_log(item) for item in value]
    if isinstance(value, str):
        return SENSITIVE_QUERY_RE.sub(r"\1=<redacted>", value)
    return value


def json_for_log(value: Any, *, max_chars: int = 4_000) -> str:
    """Serialize diagnostic data without exposing secrets or huge descriptions."""
    try:
        text = json.dumps(redact_for_log(value), ensure_ascii=False, default=str)
    except TypeError, ValueError:
        text = repr(redact_for_log(value))
    if len(text) > max_chars:
        return f"{text[:max_chars]}... <truncated {len(text) - max_chars} chars>"
    return text


class ApifyConfigurationError(RuntimeError):
    """Raised when Apify rejects the token, actor access, or paid actor setup."""


class ApifyAccountUnavailableError(ApifyConfigurationError):
    """Raised when one Apify token cannot run because auth/billing is unavailable."""


class ApifyRunError(RuntimeError):
    """Raised when an Apify actor run finishes unsuccessfully."""


class ApifyRunTimeoutError(ApifyRunError):
    """Raised when an Apify actor run exceeds the configured timeout."""


class ApifyTransientError(RuntimeError):
    """Raised for temporary Apify API errors that should be retried."""


def apify_headers(
    settings: ScraperSettings,
    token: ApifyTokenSelection | str | None = None,
) -> MutableMapping[str, str | bytes]:
    """Build authorization headers for Apify API calls."""
    return {"Authorization": f"Bearer {apify_token_value(settings, token)}"}


def apify_token_value(
    settings: ScraperSettings,
    token: ApifyTokenSelection | str | None = None,
) -> str:
    """Return the concrete token string to use for one Apify API call."""
    if isinstance(token, ApifyTokenSelection):
        return token.token
    if isinstance(token, str):
        return token

    selection = select_apify_token(settings)
    return selection.token


def select_apify_token(settings: ScraperSettings) -> ApifyTokenSelection:
    """Select the current Apify token from settings."""
    pool = getattr(settings, "apify_token_pool", None)
    if pool is not None:
        selection = pool.active()
        if selection is not None:
            return selection
        if pool.total_count:
            raise ApifyConfigurationError(
                "No configured APIFY_API_TOKEN value remains available."
            )

    token = str(getattr(settings, "apify_api_token", "") or "").strip()
    if token and token != TOKEN_PLACEHOLDER:
        return ApifyTokenSelection(0, token, 1)

    raise ApifyConfigurationError("No usable APIFY_API_TOKEN value is configured.")


def retire_apify_token(
    settings: ScraperSettings,
    token: ApifyTokenSelection,
) -> ApifyTokenSelection | None:
    """Retire one unavailable token and return the next one when configured."""
    pool = getattr(settings, "apify_token_pool", None)
    if pool is None or token.total <= 1:
        return None
    return pool.retire(token)


def apify_error_message(response: requests.Response) -> str:
    """Extract a concise user-facing error message from an Apify response."""
    try:
        data = response.json()
    except ValueError:
        return (
            response.text.strip()[:500]
            or response.reason
            or f"HTTP {response.status_code}"
        )

    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
        if data.get("message"):
            return str(data["message"])

    return str(data)[:500]


def apify_response_data(response: requests.Response) -> Any:
    """Return the Apify response payload, unwrapping the common data envelope."""
    try:
        data = response.json()
    except ValueError as exc:
        raise ApifyTransientError(
            f"Apify returned a non-JSON response for HTTP {response.status_code}: "
            f"{response.text.strip()[:500] or response.reason}"
        ) from exc
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


def apify_http_timeout(settings: ScraperSettings) -> int:
    """Return the HTTP timeout for individual Apify API calls."""
    return max(1, settings.apify_client_timeout_seconds)


def is_retryable_payment_error(response: requests.Response) -> bool:
    """Return true for Apify 402 memory-limit pressure that can clear later."""
    if response.status_code != 402:
        return False
    message = apify_error_message(response).lower()
    return "memory limit" in message and "currently used" in message


def is_apify_account_unavailable_response(response: requests.Response) -> bool:
    """Return true when a response means this token cannot currently run actors."""
    if response.status_code in (401, 403):
        return True
    return response.status_code == 402 and not is_retryable_payment_error(response)


def is_apify_credit_error_message(message: str) -> bool:
    """Return true when a run message points to exhausted billing/credits."""
    text = message.lower()
    if "memory limit" in text and "currently used" in text:
        return False
    return any(term in text for term in APIFY_CREDIT_ERROR_TERMS)


def is_retryable_apify_response(response: requests.Response) -> bool:
    """Return true when an Apify API response is likely temporary."""
    return (
        response.status_code in RETRYABLE_APIFY_HTTP_STATUS_CODES
        or is_retryable_payment_error(response)
    )


def check_apify_response(
    response: requests.Response,
    actor_id: str,
    token: ApifyTokenSelection | None = None,
) -> None:
    """Raise a user-facing exception for Apify auth/access errors."""
    if is_apify_account_unavailable_response(response):
        message = apify_error_message(response)
        token_label = token.label if token else "APIFY_API_TOKEN"
        if response.status_code in (401, 403):
            raise ApifyAccountUnavailableError(
                f"Apify rejected {token_label}. Check that the token is valid, "
                f"that its account can run {actor_id}, and that billing/trial "
                f"access is active. Apify said: {message}"
            )
        raise ApifyAccountUnavailableError(
            f"Apify said {token_label} cannot pay for {actor_id}. Apify said: {message}"
        )

    if is_retryable_apify_response(response):
        message = apify_error_message(response)
        raise ApifyTransientError(
            f"Apify returned HTTP {response.status_code} for {actor_id}: {message}"
        )

    response.raise_for_status()


def start_actor_run(
    settings: ScraperSettings,
    actor_id: str,
    payload: dict[str, Any],
    max_items: int,
    token: ApifyTokenSelection | None = None,
) -> dict[str, Any]:
    """Start a configured Apify actor and return its run metadata."""
    url = f"https://api.apify.com/v2/actors/{actor_id}/runs"
    params = {
        "timeout": settings.apify_run_timeout_seconds,
        "maxItems": max_items,
    }
    if settings.apify_run_memory_mb:
        params["memory"] = settings.apify_run_memory_mb

    LOGGER.info(
        "Starting Apify actor %s with run options %s and input %s.",
        actor_id,
        json_for_log(params),
        json_for_log(payload),
    )

    response = requests.post(
        url,
        params=params,
        headers=apify_headers(settings, token),
        json=payload,
        timeout=apify_http_timeout(settings),
    )
    check_apify_response(response, actor_id, token)

    data = apify_response_data(response)
    if not isinstance(data, dict) or not data.get("id"):
        raise ApifyRunError(f"Apify did not return a run id for actor {actor_id}.")
    LOGGER.info(
        "Apify actor %s accepted run %s (initial status=%s, dataset=%s).",
        actor_id,
        data.get("id"),
        data.get("status") or "unknown",
        data.get("defaultDatasetId") or "pending",
    )
    return data


def get_actor_run(
    settings: ScraperSettings,
    actor_id: str,
    run_id: str,
    token: ApifyTokenSelection | None = None,
) -> dict[str, Any]:
    """Fetch the latest metadata for an Apify actor run."""
    url = f"https://api.apify.com/v2/actor-runs/{run_id}"
    response = requests.get(
        url,
        headers=apify_headers(settings, token),
        timeout=apify_http_timeout(settings),
    )
    check_apify_response(response, actor_id, token)

    data = apify_response_data(response)
    if not isinstance(data, dict):
        raise ApifyRunError(f"Apify returned invalid run data for run {run_id}.")
    return data


def wait_for_actor_run(
    settings: ScraperSettings,
    actor_id: str,
    run_id: str,
    token: ApifyTokenSelection | None = None,
) -> dict[str, Any]:
    """Poll an Apify actor run until it reaches a terminal status."""
    deadline = (
        time.monotonic()
        + settings.apify_run_timeout_seconds
        + APIFY_POLL_INTERVAL_SECONDS
    )

    previous_status = ""
    while True:
        run = get_actor_run(settings, actor_id, run_id, token)
        status = str(run.get("status") or "").upper()
        if status != previous_status:
            LOGGER.debug(
                "Apify run %s for %s changed status to %s: %s",
                run_id,
                actor_id,
                status or "unknown",
                apify_run_message(run) or "no status message",
            )
            previous_status = status
        if status in APIFY_TERMINAL_STATUSES:
            if status == "SUCCEEDED":
                LOGGER.info(
                    "Apify run %s for %s finished with status SUCCEEDED (dataset=%s).",
                    run_id,
                    actor_id,
                    run.get("defaultDatasetId") or "unknown",
                )
                return run
            if status == "TIMED-OUT":
                raise ApifyRunTimeoutError(
                    f"Apify run {run_id} timed out after "
                    f"{settings.apify_run_timeout_seconds}s."
                )
            run_message = apify_run_message(run)
            if is_apify_credit_error_message(run_message):
                token_label = token.label if token else "APIFY_API_TOKEN"
                raise ApifyAccountUnavailableError(
                    f"Apify run {run_id} stopped because {token_label} cannot "
                    f"continue billing. Apify said: {run_message}"
                )
            details = f": {run_message}" if run_message else ""
            raise ApifyRunError(
                f"Apify run {run_id} finished with status {status}{details}."
            )

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ApifyRunTimeoutError(
                f"Apify run {run_id} did not finish within "
                f"{settings.apify_run_timeout_seconds}s."
            )

        time.sleep(min(APIFY_POLL_INTERVAL_SECONDS, remaining))


def fetch_dataset_items(
    settings: ScraperSettings,
    actor_id: str,
    dataset_id: str,
    max_items: int,
    token: ApifyTokenSelection | None = None,
) -> list[dict[str, Any]]:
    """Fetch JSON items from an Apify dataset."""
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    params: tuple[tuple[str, str | int], ...] = (
        ("format", "json"),
        ("limit", max_items),
    )
    response = requests.get(
        url,
        params=params,
        headers=apify_headers(settings, token),
        timeout=apify_http_timeout(settings),
    )
    check_apify_response(response, actor_id, token)

    try:
        data = response.json()
    except ValueError as exc:
        raise ApifyTransientError(
            f"Apify dataset {dataset_id} returned a non-JSON response: "
            f"{response.text.strip()[:500] or response.reason}"
        ) from exc
    if isinstance(data, list):
        items = data
    if isinstance(data, dict) and "items" in data:
        items = data["items"]
        items = items if isinstance(items, list) else []
    elif not isinstance(data, list):
        items = []

    object_items = [item for item in items if isinstance(item, dict)]
    skipped = len(items) - len(object_items)
    LOGGER.info(
        "Fetched %s dataset item(s) from %s for actor %s%s.",
        len(object_items),
        dataset_id,
        actor_id,
        f"; skipped {skipped} non-object item(s)" if skipped else "",
    )
    for index, item in enumerate(object_items[:3]):
        LOGGER.debug(
            "Raw Apify item %s/%s from %s: %s",
            index + 1,
            len(object_items),
            actor_id,
            json_for_log(item),
        )
    return object_items


def run_actor(
    settings: ScraperSettings, actor_id: str, payload: dict[str, Any], max_items: int
) -> list[dict[str, Any]]:
    """Run a configured Apify actor and return its dataset items."""
    while True:
        token = select_apify_token(settings)
        try:
            run = start_actor_run(settings, actor_id, payload, max_items, token)
            run_id = str(run["id"])
            completed_run = wait_for_actor_run(settings, actor_id, run_id, token)
            dataset_id = completed_run.get("defaultDatasetId") or run.get(
                "defaultDatasetId"
            )
            if not dataset_id:
                raise ApifyRunError(
                    f"Apify run {run_id} did not include a default dataset id."
                )
            items = fetch_dataset_items(
                settings,
                actor_id,
                str(dataset_id),
                max_items,
                token,
            )
            if not items:
                LOGGER.warning(
                    "Apify actor %s run %s succeeded but dataset %s returned zero "
                    "items. Input was %s. Check actor logs, search breadth, date "
                    "filters, and input-schema compatibility.",
                    actor_id,
                    run_id,
                    dataset_id,
                    json_for_log(payload),
                )
            return items
        except ApifyAccountUnavailableError as exc:
            next_token = retire_apify_token(settings, token)
            if next_token is None:
                if token.total > 1:
                    raise ApifyConfigurationError(
                        "No configured APIFY_API_TOKEN value can currently run "
                        f"{actor_id}. Tried {token.total} token(s). Last error: {exc}"
                    ) from exc
                raise

            LOGGER.warning(
                "%s cannot currently run Apify actor %s: %s Switching to %s.",
                token.label,
                actor_id,
                exc,
                next_token.label,
            )


def retry_delay_seconds(settings: ScraperSettings, attempt: int) -> int:
    """Return the backoff delay before retrying a transient Apify issue."""
    if settings.apify_retry_delay_seconds <= 0:
        return 0
    return min(
        settings.apify_retry_delay_seconds * (2 ** max(0, attempt - 1)),
        MAX_APIFY_RETRY_DELAY_SECONDS,
    )


def apify_run_message(run: dict[str, Any]) -> str:
    """Extract a useful status/error message from Apify run metadata."""
    candidates = [
        run.get("statusMessage"),
        run.get("statusDetails"),
        run.get("message"),
        run.get("errorMessage"),
        run.get("error"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        if isinstance(candidate, dict):
            nested_message = candidate.get("message") or candidate.get("detail")
            if nested_message:
                return str(nested_message).strip()
    return ""

from __future__ import annotations
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential_jitter, retry_any
import requests
from gspread import exceptions as gse

# ---------- Predicates ----------

def _is_retryable_requests(e: Exception) -> bool:
    # Network hiccups
    if isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    # HTTP responses with retryable status codes
    if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
        code = e.response.status_code
        return code in (429, 500, 502, 503, 504)
    return False

def _is_retryable_gspread(e: Exception) -> bool:
    if isinstance(e, gse.APIError):
        # Status code based
        code = getattr(getattr(e, "response", None), "status_code", None)
        if code in (429, 500, 502, 503, 504):
            return True
        # Some Google APIs signal rate limit via 403 with a reason
        try:
            payload = e.response.json() if getattr(e, "response", None) else {}
            reason = (payload.get("error", {})
                             .get("errors", [{}])[0]
                             .get("reason"))
            if code == 403 and reason in {"rateLimitExceeded", "userRateLimitExceeded", "quotaExceeded"}:
                return True
        except Exception:
            pass
    return False

# ---------- Decorators ----------

def retry_read_api(func):
    """For idempotent reads (GET). Retries only on transient conditions."""
    return retry(
        retry=retry_any(
            retry_if_exception(_is_retryable_requests),
            retry_if_exception(_is_retryable_gspread),
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(1, 5),
        reraise=True,
    )(func)

def retry_write_api(func):
    """
    For writes (POST/PUT/PATCH) where you have idempotency in place OR accept minimal duplicate risk.
    Retries on transient conditions only, with conservative attempts.
    """
    return retry(
        retry=retry_any(
            retry_if_exception(_is_retryable_requests),
            retry_if_exception(_is_retryable_gspread),
        ),
        stop=stop_after_attempt(2),   # slightly stricter for writes
        wait=wait_exponential_jitter(1, 4),
        reraise=True,
    )(func)

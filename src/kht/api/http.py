"""Small resilient HTTP layer shared by every Polymarket client.

Polymarket's public APIs are throttled per IP (see docs/api-reference/rate-limits),
so all requests funnel through a per-host token bucket and a retry loop with
exponential backoff. Sessions are kept per thread, which makes the client safe
to use from a thread pool.
"""

from __future__ import annotations

import random
import threading
import time
from typing import Any
from urllib.parse import urlsplit

import requests

USER_AGENT = "kht/0.1 (research client)"

# Requests per second we allow ourselves per host. These sit well under the
# published limits (e.g. data-api /v2/prices-history is 20 req/s, gamma
# /markets is 30 req/s) so that a long download never trips the throttle.
DEFAULT_RATE_PER_HOST = {
    "gamma-api.polymarket.com": 10.0,
    "data-api.polymarket.com": 12.0,
    "clob.polymarket.com": 20.0,
    "polymarket.com": 2.0,
}
FALLBACK_RATE = 5.0

RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504, 520, 522, 524}


class HttpError(RuntimeError):
    def __init__(self, status: int, url: str, body: str):
        super().__init__(f"HTTP {status} for {url}: {body[:300]}")
        self.status = status
        self.url = url
        self.body = body


class _TokenBucket:
    """Thread-safe token bucket; ``acquire`` blocks until a token is free."""

    def __init__(self, rate: float, burst: float | None = None):
        self.rate = float(rate)
        self.capacity = float(burst if burst is not None else max(1.0, rate))
        self._tokens = self.capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                self._tokens = min(self.capacity, self._tokens + (now - self._last) * self.rate)
                self._last = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / self.rate
            time.sleep(wait)


class Http:
    """GET/POST JSON with rate limiting, retries and per-thread sessions."""

    def __init__(
        self,
        rate_per_host: dict[str, float] | None = None,
        timeout: float = 45.0,
        max_retries: int = 6,
    ):
        self._rates = dict(DEFAULT_RATE_PER_HOST)
        if rate_per_host:
            self._rates.update(rate_per_host)
        self._buckets: dict[str, _TokenBucket] = {}
        self._buckets_lock = threading.Lock()
        self._local = threading.local()
        self.timeout = timeout
        self.max_retries = max_retries
        self.request_count = 0
        self.retry_count = 0

    def _session(self) -> requests.Session:
        s = getattr(self._local, "session", None)
        if s is None:
            s = requests.Session()
            s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
            self._local.session = s
        return s

    def _bucket(self, host: str) -> _TokenBucket:
        with self._buckets_lock:
            b = self._buckets.get(host)
            if b is None:
                b = _TokenBucket(self._rates.get(host, FALLBACK_RATE))
                self._buckets[host] = b
            return b

    def request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        host = urlsplit(url).netloc
        bucket = self._bucket(host)
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            bucket.acquire()
            self.request_count += 1
            try:
                resp = self._session().request(
                    method, url, params=params, json=json_body, headers=headers, timeout=self.timeout
                )
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
            else:
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except ValueError as exc:  # truncated / non-JSON body
                        last_exc = exc
                elif resp.status_code in RETRYABLE_STATUS:
                    last_exc = HttpError(resp.status_code, resp.url, resp.text)
                else:
                    raise HttpError(resp.status_code, resp.url, resp.text)
            if attempt < self.max_retries:
                self.retry_count += 1
                time.sleep(min(30.0, (2**attempt) * 0.5) + random.uniform(0, 0.25))
        assert last_exc is not None
        raise last_exc

    def get(self, url: str, params: dict[str, Any] | None = None, **kw: Any) -> Any:
        return self.request("GET", url, params=params, **kw)

    def post(self, url: str, json_body: Any = None, **kw: Any) -> Any:
        return self.request("POST", url, json_body=json_body, **kw)

"""Read-only clients for Polymarket's public market-data APIs.

Three services are involved (all public, no credentials needed):

* Gamma API   - market / event discovery and metadata
* Data API v2 - price history, trade tapes, holders, leaderboards
* CLOB API    - live order books, midpoints, spreads

Endpoint shapes follow https://docs.polymarket.com (checked November 2026).
Everything here is read-only; order placement lives in ``kht.exec``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from .http import Http, HttpError

GAMMA = "https://gamma-api.polymarket.com"
DATA = "https://data-api.polymarket.com/v2"
CLOB = "https://clob.polymarket.com"
SITE = "https://polymarket.com"

# Price-history grains the Data API stores. Coarse grains are permanent, the
# fine ones are windowed (minimums: 60s >= 7 days, 300s >= 60 days,
# 1800s >= 90 days). Explicit start/end windows are capped at 15 days.
PERMANENT_BUCKETS = (10_800, 43_200)
MAX_RANGE_SECONDS = 15 * 86_400


def parse_json_list(value: Any) -> list[Any]:
    """Gamma encodes several list fields (outcomes, clobTokenIds...) as JSON strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        out = json.loads(value)
    except (TypeError, ValueError):
        return []
    return out if isinstance(out, list) else []


class Polymarket:
    def __init__(self, http: Http | None = None):
        self.http = http or Http()

    # ------------------------------------------------------------------ Gamma
    def iter_markets(self, max_pages: int | None = None, **filters: Any) -> Iterator[dict[str, Any]]:
        """Iterate markets with keyset pagination (100 per page).

        Common filters: closed, volume_num_min, end_date_min/max,
        start_date_min/max, tag_id, sports_market_types, include_tag.
        """
        yield from self._iter_keyset("/markets/keyset", "markets", max_pages, filters)

    def iter_events(self, max_pages: int | None = None, **filters: Any) -> Iterator[dict[str, Any]]:
        """Iterate events with keyset pagination. Beware: events embed all
        their markets, so game events can be >1 MB each."""
        yield from self._iter_keyset("/events/keyset", "events", max_pages, filters)

    def _iter_keyset(
        self, path: str, key: str, max_pages: int | None, filters: dict[str, Any]
    ) -> Iterator[dict[str, Any]]:
        params = {k: _encode(v) for k, v in filters.items() if v is not None}
        params.setdefault("limit", 100)
        cursor: str | None = None
        pages = 0
        while True:
            page_params = dict(params)
            if cursor:
                page_params["after_cursor"] = cursor
            payload = self.http.get(GAMMA + path, page_params)
            items = payload.get(key) or []
            yield from items
            pages += 1
            cursor = payload.get("next_cursor")
            if not cursor or not items or (max_pages is not None and pages >= max_pages):
                return

    def event_by_slug(self, slug: str) -> dict[str, Any]:
        return self.http.get(f"{GAMMA}/events/slug/{slug}")

    def market_by_id(self, market_id: str | int) -> dict[str, Any]:
        return self.http.get(f"{GAMMA}/markets/{market_id}")

    def sports(self) -> list[dict[str, Any]]:
        return self.http.get(f"{GAMMA}/sports")

    def tags(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        return self.http.get(f"{GAMMA}/tags", {"limit": limit, "offset": offset})

    # --------------------------------------------------------------- Data API
    def prices_history(
        self,
        token_id: str,
        *,
        interval: str | None = None,
        start: int | None = None,
        end: int | None = None,
        bucket_seconds: int | None = None,
    ) -> list[tuple[int, float]]:
        """Price series for one outcome token as ``[(epoch_seconds, price), ...]``.

        Pass either ``interval`` ("max" for the whole life) or ``start``/``end``
        (at most 15 days). Follows cursors until the series is complete.
        """
        params: dict[str, Any] = {"token_id": token_id}
        if interval is not None:
            params["interval"] = interval
        if start is not None:
            params["start"] = int(start)
        if end is not None:
            params["end"] = int(end)
        if bucket_seconds is not None:
            params["bucket_seconds"] = int(bucket_seconds)
        out: list[tuple[int, float]] = []
        while True:
            payload = self.http.get(f"{DATA}/prices-history", params)
            out.extend((int(p["timestamp"]), float(p["price"])) for p in payload.get("data") or [])
            pag = payload.get("pagination") or {}
            if not pag.get("has_more") or not pag.get("next_cursor"):
                return out
            params = dict(params, cursor=pag["next_cursor"])

    def prices_history_range(
        self, token_id: str, start: int, end: int, bucket_seconds: int
    ) -> list[tuple[int, float]]:
        """Fine-grained history over an arbitrary span, walking 15-day windows."""
        out: list[tuple[int, float]] = []
        lo = int(start)
        while lo < end:
            hi = min(int(end), lo + MAX_RANGE_SECONDS - 1)
            out.extend(self.prices_history(token_id, start=lo, end=hi, bucket_seconds=bucket_seconds))
            lo = hi
        # windows are [start, end) so there are no duplicates, but be defensive
        seen: set[int] = set()
        dedup = []
        for ts, px in out:
            if ts not in seen:
                seen.add(ts)
                dedup.append((ts, px))
        dedup.sort()
        return dedup

    def iter_trades(
        self, *, condition: str | None = None, event_id: str | None = None,
        page_size: int = 1000, max_pages: int | None = None, taker_only: bool = True,
    ) -> Iterator[dict[str, Any]]:
        """Trade tape for a market (newest first). Covers a fixed 3-year window."""
        base: dict[str, Any] = {"limit": page_size}
        if condition:
            base["condition"] = condition
        if event_id:
            base["event_id"] = event_id
        if not taker_only:
            base["taker_only"] = "false"
        params = dict(base)
        pages = 0
        while True:
            payload = self.http.get(f"{DATA}/trades", params)
            items = payload.get("data") or []
            if condition:
                # The cursor does NOT carry the market filter: a cursor sent on
                # its own silently continues through the global trade feed. The
                # filter is therefore re-sent with every page, and rows are
                # checked so that a regression can never pollute a tape.
                stray = [t for t in items if t.get("condition_id") != condition]
                if stray:
                    raise RuntimeError(f"trade feed returned {len(stray)} rows for other markets")
            yield from items
            pages += 1
            pag = payload.get("pagination") or {}
            if not items or not pag.get("has_more") or not pag.get("next_cursor"):
                return
            if max_pages is not None and pages >= max_pages:
                return
            params = dict(base, cursor=pag["next_cursor"])

    def open_interest(self, condition: str) -> Any:
        return self.http.get(f"{DATA}/oi", {"condition": condition})

    # ------------------------------------------------------------------- CLOB
    def book(self, token_id: str) -> dict[str, Any]:
        return self.http.get(f"{CLOB}/book", {"token_id": token_id})

    def books(self, token_ids: list[str]) -> list[dict[str, Any]]:
        """Batch order books (max 500 per request)."""
        out: list[dict[str, Any]] = []
        for i in range(0, len(token_ids), 500):
            chunk = token_ids[i : i + 500]
            out.extend(self.http.post(f"{CLOB}/books", [{"token_id": t} for t in chunk]))
        return out

    def clob_time(self) -> int:
        return int(self.http.get(f"{CLOB}/time"))

    # ------------------------------------------------------------------- site
    def geoblock(self) -> dict[str, Any]:
        """Whether *this machine's IP* may place orders. Trading code must check
        this and refuse to run when blocked; it must never be worked around."""
        return self.http.get(f"{SITE}/api/geoblock")


def _encode(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def best_bid_ask(book: dict[str, Any]) -> tuple[float | None, float | None, float, float]:
    """Return (best_bid, best_ask, bid_size, ask_size) from a CLOB book payload.

    The API orders bids ascending and asks descending, so the best level is
    the last entry of each; we take max/min explicitly to not depend on that.
    """
    bids = [(float(l["price"]), float(l["size"])) for l in book.get("bids") or []]
    asks = [(float(l["price"]), float(l["size"])) for l in book.get("asks") or []]
    bid = max(bids, default=None)
    ask = min(asks, default=None)
    return (
        bid[0] if bid else None,
        ask[0] if ask else None,
        bid[1] if bid else 0.0,
        ask[1] if ask else 0.0,
    )


__all__ = ["Polymarket", "HttpError", "parse_json_list", "best_bid_ask", "GAMMA", "DATA", "CLOB"]

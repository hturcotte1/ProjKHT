"""Read-only client for Polymarket US, the exchange open to US residents.

Polymarket US is a separate venue from polymarket.com in every way that
matters here: its own markets, order books, fees, accounts and API. Nothing
measured on one says anything certain about the other.

Everything in this module uses the public gateway, which needs no key and
serves market lists, order books, settlement prices and book-derived price
history. Placing orders needs a key and is deliberately not implemented.

Docs: https://docs.polymarket.us (index at /llms.txt).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .http import Http

GATEWAY = "https://gateway.polymarket.us"
PAGE = 500                      # the gateway returns at most 500 markets a page
RATE = 12.0                     # requests a second; the published public limit is 20 an IP

# Fee = theta * contracts * price * (1 - price) for the order that takes
# liquidity; resting orders pay nothing. Theta depends on the account's
# taker volume over the last 30 days (docs.polymarket.us/fees, effective
# 28 October 2026). A small account is in the first tier.
TAKER_THETA = {0: 0.095, 10_000: 0.085, 50_000: 0.075, 250_000: 0.0695}


def taker_fee_per_share(price: float, theta: float = 0.095) -> float:
    """Taker fee for one contract bought or sold at ``price`` (unrounded; orders round to the cent)."""
    return theta * price * (1.0 - price)


class PolymarketUS:
    def __init__(self, http: Http | None = None):
        self.http = http or Http(rate_per_host={"gateway.polymarket.us": RATE})

    # ------------------------------------------------------------- listings
    def _paged(self, path: str, key: str, max_pages: int | None, filters: dict[str, Any]) -> Iterator[dict[str, Any]]:
        offset, pages = 0, 0
        while max_pages is None or pages < max_pages:
            params = {"limit": PAGE, "offset": offset, **{k: _encode(v) for k, v in filters.items() if v is not None}}
            rows = (self.http.get(GATEWAY + path, params=params) or {}).get(key) or []
            yield from rows
            # Only an empty page ends the listing. A page can come back a row or
            # two short of the limit with more behind it (the gateway seems to drop
            # hidden rows after cutting the page), and stopping there loses everything after.
            if not rows:
                return
            offset += PAGE
            pages += 1

    def iter_markets(self, max_pages: int | None = None, **filters: Any) -> Iterator[dict[str, Any]]:
        """Markets matching ``filters`` (closed, active, categories, endDateMin, endDateMax, orderBy ...)."""
        return self._paged("/v1/markets", "markets", max_pages, filters)

    def iter_events(self, max_pages: int | None = None, **filters: Any) -> Iterator[dict[str, Any]]:
        return self._paged("/v1/events", "events", max_pages, filters)

    def iter_incentives(self, statuses: str | None = "active", max_pages: int = 1000) -> Iterator[dict[str, Any]]:
        """The public schedule of reward programmes, one entry per market with its time periods.

        Each time period carries the programme's id, its reward pool, the
        discount factor, the target size and (for some) a maximum spread. A
        pool belongs to the programme, shared across its markets: the same
        number is repeated on every market, and must never be added up.
        """
        token: str | None = None
        for _ in range(max_pages):
            params: dict[str, Any] = {"page_size": PAGE}
            if statuses:
                params["statuses"] = statuses
            if token:
                params["page_token"] = token
            data = self.http.get(GATEWAY + "/v1/incentives", params=params) or {}
            rows = data.get("programs") or []
            yield from rows
            token = data.get("nextPageToken")
            if not token or not rows:
                return

    def market(self, slug: str) -> dict[str, Any]:
        return (self.http.get(f"{GATEWAY}/v1/market/slug/{slug}") or {}).get("market") or {}

    # ------------------------------------------------------- one market's data
    def bbo(self, slug: str) -> dict[str, Any]:
        """Best bid and ask, last trade, shares traded, open interest and (once settled) the settlement price."""
        return (self.http.get(f"{GATEWAY}/v1/markets/{slug}/bbo") or {}).get("marketData") or {}

    def book(self, slug: str) -> dict[str, Any]:
        return (self.http.get(f"{GATEWAY}/v1/markets/{slug}/book") or {}).get("marketData") or {}

    def settlement(self, slug: str) -> float | None:
        """What the "Yes" side paid: 1.0, 0.0, or something between for a split; None if not settled."""
        try:
            value = (self.http.get(f"{GATEWAY}/v1/markets/{slug}/settlement") or {}).get("settlement")
        except Exception:
            return None
        return None if value is None else float(value)

    def price_history(self, slug: str, interval: str = "INTERVAL_ALL", fidelity: int = 180) -> list[tuple[int, float, float]]:
        """(timestamp, ask of "Yes", ask of "No") observations of the order book.

        These are quotes, not trades: the "Yes" price is the best ask and the
        "No" price is one minus the best bid, so the two add up to more than
        one by the spread. ``INTERVAL_ALL`` returns one point a day over the
        market's whole life; ``INTERVAL_1M`` one every three hours for the
        last 30 days.
        """
        data = self.http.get(f"{GATEWAY}/v1/price-history", params={"symbol": slug, "fixedInterval": interval, "fidelity": fidelity})
        return _points(data)

    def price_history_window(self, slug: str, start_ts: int, end_ts: int) -> list[tuple[int, float, float]]:
        """Minute-by-minute observations between two times at most a day apart."""
        data = self.http.get(f"{GATEWAY}/v1/price-history", params={"symbol": slug, "fidelity": 1, "timestamp.startTimestamp": int(start_ts),
                                                                    "timestamp.endTimestamp": int(end_ts)})
        return _points(data)


def _points(data: Any) -> list[tuple[int, float, float]]:
    out = []
    for p in (data or {}).get("history") or []:
        try:
            out.append((int(p["timestamp"]), float(p["longPrice"]), float(p["shortPrice"])))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _encode(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def yes_settlement(market: dict[str, Any]) -> float | None:
    """What "Yes" paid, read from a listed market: its first outcome price once the market is resolved."""
    if market.get("status") != "MARKET_STATUS_RESOLVED":
        return None
    prices = market.get("outcomePrices")
    if isinstance(prices, str):
        import json

        try:
            prices = json.loads(prices)
        except ValueError:
            return None
    try:
        return float(prices[0])
    except (IndexError, TypeError, ValueError):
        return None

"""Live broker for Polymarket US: real resting orders through the exchange's API.

STATUS: written from the published API reference and the exchange's own
Python SDK (docs.polymarket.us, read on 11 November 2026), and exercised in
tests against a stand-in for the network. **It has never been run against
the exchange.** No credentials were available when it was written. Before
it is trusted with money, follow the steps in docs/10_us_quoter.md: a
preview run that sends nothing, then one order of one contract by hand.

Live trading is deliberately hard to switch on. All of these must hold:

1. the environment has ``KHT_ENABLE_LIVE=yes-trade-real-money``;
2. ``POLYMARKET_US_KEY_ID`` and ``POLYMARKET_US_SECRET_KEY`` are set, in
   the environment only: never in the repository, never in a config file;
3. the ``cryptography`` package is installed (``pip install -e ".[live-us]"``).

What it will and will not do:

* every order is a limit order that may only rest
  (``participateDontInitiate``), so it never pays the taker fee and never
  takes a price; the exchange rejects it if it would trade at once;
* every order carries its own expiry (good-till-date), so it leaves the
  book by itself if this program stops;
* an order's price is always the price of "Yes", as the API defines it, and
  is refused here outside 1c to 99c or above ``us_quoter.MAX_SIZE`` contracts;
* order requests are sent once. They are not retried, because a retry of a
  request whose answer was lost could place the order twice. The engine
  reads the open orders again at the next cycle and works from that;
* "cancel everything" is only ever sent with a list of markets. An empty
  list would cancel every order on the account, and is refused.
"""

from __future__ import annotations

import base64
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable

import requests

from .us_quoter import BUY_NO, BUY_YES, MAX_SIZE, SELL_NO, SELL_YES, Order, Position, Want
from .us_rewards import _when

API = "https://api.polymarket.us"
ENABLE_ENV, ENABLE_VALUE = "KHT_ENABLE_LIVE", "yes-trade-real-money"
KEY_ENV, SECRET_ENV = "POLYMARKET_US_KEY_ID", "POLYMARKET_US_SECRET_KEY"
BATCH = 20                      # the most orders the API takes in one request
BIDS, ASKS = {BUY_YES, SELL_NO}, {SELL_YES, BUY_NO}


class LiveTradingNotPermitted(RuntimeError):
    pass


def preflight(env: dict[str, str] | None = None) -> tuple[str, str]:
    """Raise unless every precondition for live trading holds. Returns the key id and the secret."""
    env = dict(os.environ) if env is None else env
    if env.get(ENABLE_ENV) != ENABLE_VALUE:
        raise LiveTradingNotPermitted(f"live trading is off: set {ENABLE_ENV}={ENABLE_VALUE} to enable it")
    for key in (KEY_ENV, SECRET_ENV):
        if not env.get(key):
            raise LiveTradingNotPermitted(f"missing credential {key} in the environment")
    return env[KEY_ENV], env[SECRET_ENV]


def signer(secret_key: str) -> Callable[[bytes], bytes]:
    """A function that signs with the account's Ed25519 key (the exchange gives it out base64-encoded)."""
    raw = base64.b64decode(secret_key)
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError as exc:                      # pragma: no cover - depends on the installation
        raise LiveTradingNotPermitted('signing needs the "cryptography" package: pip install -e ".[live-us]"') from exc
    return ed25519.Ed25519PrivateKey.from_private_bytes(raw[:32]).sign


def auth_headers(key_id: str, sign: Callable[[bytes], bytes], method: str, path: str, now_ms: int) -> dict[str, str]:
    """The three headers the API asks for. The signature covers the time, the method and the path, without any query."""
    stamp = str(now_ms)
    return {"X-PM-Access-Key": key_id, "X-PM-Timestamp": stamp,
            "X-PM-Signature": base64.b64encode(sign(f"{stamp}{method}{path}".encode())).decode(), "Content-Type": "application/json"}


def order_body(w: Want) -> dict[str, Any]:
    """One order as the API wants it. Raises rather than send anything outside the limits."""
    if w.intent not in BIDS | ASKS or (w.intent in BIDS) != (w.side == "bid"):
        raise ValueError(f"order kind {w.intent} does not rest on the {w.side} side")
    if not 0.01 - 1e-9 <= w.price <= 0.99 + 1e-9:
        raise ValueError(f"price {w.price} is outside 1c to 99c")
    if not 1.0 <= w.qty <= MAX_SIZE:
        raise ValueError(f"size {w.qty} is outside 1 to {MAX_SIZE:g} contracts")
    if w.expires <= time.time():
        raise ValueError("the order would already have expired")
    return {"marketSlug": w.slug, "type": "ORDER_TYPE_LIMIT", "price": {"value": f"{w.price:.4f}".rstrip("0").rstrip("."), "currency": "USD"},
            "quantity": w.qty, "tif": "TIME_IN_FORCE_GOOD_TILL_DATE",
            "goodTillTime": datetime.fromtimestamp(w.expires, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "intent": w.intent, "participateDontInitiate": True, "manualOrderIndicator": "MANUAL_ORDER_INDICATOR_AUTOMATIC"}


class LiveUSBroker:
    """Sends the quoting engine's orders to Polymarket US. See the module's warning before using it."""

    def __init__(self, key_id: str, sign: Callable[[bytes], bytes], session: Any = None, preview: bool = False,
                 clock: Callable[[], float] = time.time, timeout: float = 15.0):
        self.key_id, self.sign, self.preview, self.clock, self.timeout = key_id, sign, preview, clock, timeout
        self.http = session or requests.Session()
        self.previews: list[Any] = []

    @classmethod
    def from_env(cls, preview: bool = False, env: dict[str, str] | None = None) -> "LiveUSBroker":
        key_id, secret = preflight(env)
        return cls(key_id, signer(secret), preview=preview)

    # ------------------------------------------------------------------ the wire
    def _call(self, method: str, path: str, body: Any = None, params: dict[str, Any] | None = None) -> Any:
        tries = 3 if method == "GET" else 1          # reading can be repeated safely; an order request cannot
        last: Exception | None = None
        for attempt in range(tries):
            headers = auth_headers(self.key_id, self.sign, method, path, int(self.clock() * 1000))
            try:
                resp = self.http.request(method, API + path, json=body, params=params, headers=headers, timeout=self.timeout)
            except requests.RequestException as exc:
                last = exc
            else:
                if resp.status_code == 200:
                    return resp.json() if resp.content else {}
                last = RuntimeError(f"HTTP {resp.status_code} for {method} {path}: {resp.text[:300]}")
                if resp.status_code not in (429, 500, 502, 503, 504):
                    break
            if attempt + 1 < tries:
                time.sleep(0.5 * (attempt + 1))
        assert last is not None
        raise last

    # ------------------------------------------------------------------ reading
    def open_orders(self, slugs: list[str]) -> list[Order]:
        """Every open order of the account in these markets. The engine treats all of them as its own."""
        want = set(slugs)
        out = []
        for o in (self._call("GET", "/v1/orders/open") or {}).get("orders") or []:
            if o.get("marketSlug") not in want:
                continue
            intent = o.get("intent") or ""
            left = o.get("leavesQuantity")
            out.append(Order(str(o.get("id")), o["marketSlug"], "bid" if intent in BIDS else "ask", intent, float((o.get("price") or {}).get("value")),
                             float(left if left is not None else o.get("quantity") or 0.0), _when(o.get("goodTillTime")) or 0.0))
        return out

    def positions(self) -> dict[str, Position]:
        """What each market's orders have been filled. The dollars at risk are an upper bound: a dollar a contract held."""
        out: dict[str, Position] = {}
        cursor: str | None = None
        for _ in range(50):
            page = self._call("GET", "/v1/portfolio/positions", params={"cursor": cursor} if cursor else None) or {}
            for slug, p in (page.get("positions") or {}).items():
                bought, sold = float(p.get("qtyBoughtDecimal") or 0.0), float(p.get("qtySoldDecimal") or 0.0)
                if p.get("expired") or (bought == 0.0 and sold == 0.0):
                    continue
                net = bought - sold
                # what was paid and received is not in the answer in a form that has been checked, so the bound is used:
                # a long position cannot lose more than a dollar a contract, nor a short one
                out[slug] = Position(bought=bought, sold=sold, cost=max(net, 0.0), proceeds=0.0)
            cursor = page.get("nextCursor")
            if page.get("eof", True) or not cursor:
                break
        return out

    def equity(self, marks: dict[str, float]) -> float | None:
        """Buying power plus what the positions are worth, as the exchange's own pages define the account's value. Not checked against a real account."""
        balances = (self._call("GET", "/v1/account/balances") or {}).get("balances") or []
        usd = next((b for b in balances if (b.get("currency") or "USD") == "USD"), None)
        if usd is None or usd.get("buyingPower") is None:
            return None
        return float(usd["buyingPower"]) + float(usd.get("assetNotional") or 0.0)

    def earnings(self, start_date: str | None = None) -> list[dict[str, Any]]:
        """What the exchange says the account earned in rewards, by market and date. This is the number the whole idea waits on."""
        params = {"start_date": start_date, "program_type": "liquidityProgram"} if start_date else {"program_type": "liquidityProgram"}
        return (self._call("GET", "/v1/incentives/earnings", params=params) or {}).get("rewards") or []

    # ------------------------------------------------------------------ orders
    def place(self, wants: list[Want]) -> list[str]:
        bodies = [order_body(w) for w in wants]      # every order is checked before any is sent
        if self.preview:
            for b in bodies:
                self.previews.append(self._call("POST", "/v1/order/preview", body=b))
            return []
        ids: list[str] = []
        for i in range(0, len(bodies), BATCH):
            ids += (self._call("POST", "/v1/orders/batched", body={"orders": bodies[i:i + BATCH]}) or {}).get("createdOrderIds") or []
        return ids

    def cancel(self, orders: list[Order]) -> None:
        if self.preview:
            return
        entries = [{"orderId": o.id, "marketSlug": o.slug} for o in orders]
        for i in range(0, len(entries), BATCH):
            self._call("POST", "/v1/orders/batched/cancel", body={"orders": entries[i:i + BATCH]})

    def cancel_all(self, slugs: list[str]) -> None:
        """Cancel every open order in these markets. Never called without a list: that would empty the whole account's book."""
        if self.preview or not slugs:
            return
        for i in range(0, len(slugs), 100):
            self._call("POST", "/v1/orders/open/cancel", body={"slugs": slugs[i:i + 100]})

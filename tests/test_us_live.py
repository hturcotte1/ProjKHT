"""The live broker for Polymarket US, against a stand-in for the network. It has never met the real exchange."""

from __future__ import annotations

import base64
import time

import pytest

from kht.trading import us_live as live
from kht.trading import us_quoter as uq

ed25519 = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.ed25519")

SEED = bytes(range(32))
SECRET = base64.b64encode(SEED).decode()
LATER = time.time() + 600


class Resp:
    def __init__(self, status=200, payload=None):
        self.status_code, self._payload = status, payload if payload is not None else {}
        self.content = b"x"
        self.text = str(payload)

    def json(self):
        return self._payload


class Session:
    """Answers each request from a queue of responses for its path, and remembers what it was sent."""

    def __init__(self, answers=None):
        self.answers = answers or {}
        self.sent = []

    def request(self, method, url, json=None, params=None, headers=None, timeout=None):
        path = url.replace(live.API, "")
        self.sent.append({"method": method, "path": path, "json": json, "params": params, "headers": headers})
        queue = self.answers.get(path)
        if not queue:
            return Resp(200, {})
        return queue.pop(0) if len(queue) > 1 else queue[0]


def broker(session, preview=False):
    return live.LiveUSBroker("key-1", live.signer(SECRET), session=session, preview=preview, clock=lambda: 1_794_400_000.0)


def want(side="bid", intent=uq.BUY_YES, price=0.45, qty=100.0, slug="aec-itfme-a-b-2026-11-12", expires=None):
    return uq.Want(slug, side, intent, price, qty, expires or LATER)


def test_live_trading_is_off_unless_everything_is_set():
    with pytest.raises(live.LiveTradingNotPermitted):
        live.preflight({})
    with pytest.raises(live.LiveTradingNotPermitted):
        live.preflight({live.ENABLE_ENV: live.ENABLE_VALUE, live.KEY_ENV: "k"})
    with pytest.raises(live.LiveTradingNotPermitted):
        live.preflight({live.ENABLE_ENV: "yes", live.KEY_ENV: "k", live.SECRET_ENV: SECRET})
    assert live.preflight({live.ENABLE_ENV: live.ENABLE_VALUE, live.KEY_ENV: "k", live.SECRET_ENV: SECRET}) == ("k", SECRET)


def test_the_signature_covers_the_time_the_method_and_the_path():
    h = live.auth_headers("key-1", live.signer(SECRET), "POST", "/v1/orders/batched", 1_794_400_000_123)
    assert h["X-PM-Access-Key"] == "key-1" and h["X-PM-Timestamp"] == "1794400000123"
    public = ed25519.Ed25519PrivateKey.from_private_bytes(SEED).public_key()
    public.verify(base64.b64decode(h["X-PM-Signature"]), b"1794400000123POST/v1/orders/batched")       # raises if it does not verify
    # a 64-byte secret, as some tools give it, signs the same: only the first 32 bytes are the key
    long_secret = base64.b64encode(SEED + bytes(32)).decode()
    assert live.auth_headers("key-1", live.signer(long_secret), "POST", "/v1/orders/batched", 1_794_400_000_123) == h


def test_an_order_is_sent_as_one_that_may_only_rest_and_that_expires():
    b = live.order_body(want(expires=LATER))
    assert b["marketSlug"] == "aec-itfme-a-b-2026-11-12" and b["type"] == "ORDER_TYPE_LIMIT" and b["price"] == {"value": "0.45", "currency": "USD"}
    assert b["quantity"] == 100.0 and b["intent"] == "ORDER_INTENT_BUY_LONG"
    assert b["participateDontInitiate"] is True and b["tif"] == "TIME_IN_FORCE_GOOD_TILL_DATE" and b["goodTillTime"].endswith("Z")
    assert b["manualOrderIndicator"] == "MANUAL_ORDER_INDICATOR_AUTOMATIC"
    assert live.order_body(want("ask", uq.BUY_NO, 0.47))["price"]["value"] == "0.47"                     # an offer carries the price of "Yes" too
    assert live.order_body(want(price=0.455))["price"]["value"] == "0.455"


@pytest.mark.parametrize("bad", [want(price=0.995), want(price=0.0), want(qty=0.5), want(qty=5000.0), want(side="ask", intent=uq.BUY_YES),
                                 want(side="bid", intent=uq.BUY_NO), want(intent="ORDER_INTENT_SOMETHING"), want(expires=time.time() - 5)])
def test_an_order_outside_the_limits_is_refused_before_anything_is_sent(bad):
    s = Session()
    with pytest.raises(ValueError):
        broker(s).place([want(), bad])
    assert s.sent == []                                                                                  # not even the good one went


def test_orders_go_out_twenty_at_a_time_and_are_never_retried():
    s = Session({"/v1/orders/batched": [Resp(200, {"createdOrderIds": [str(i) for i in range(20)]}), Resp(200, {"createdOrderIds": ["20", "21", "22"]})]})
    ids = broker(s).place([want(slug=f"m{i}") for i in range(23)])
    assert len(ids) == 23 and [len(x["json"]["orders"]) for x in s.sent] == [20, 3]
    assert all(x["method"] == "POST" and x["path"] == "/v1/orders/batched" for x in s.sent)
    failing = Session({"/v1/orders/batched": [Resp(503, "busy")]})
    with pytest.raises(RuntimeError):
        broker(failing).place([want()])
    assert len(failing.sent) == 1                                                                        # once, and no more


def test_a_preview_run_sends_no_order():
    s = Session({"/v1/order/preview": [Resp(200, {"ok": True})]})
    b = broker(s, preview=True)
    assert b.place([want(), want("ask", uq.BUY_NO, 0.47)]) == []
    b.cancel([uq.Order("9", "m", "bid", uq.BUY_YES, 0.45, 100.0, LATER)])
    b.cancel_all(["m"])
    assert [x["path"] for x in s.sent] == ["/v1/order/preview", "/v1/order/preview"] and len(b.previews) == 2


def test_cancelling_is_by_order_and_never_the_whole_account():
    s = Session()
    b = broker(s)
    b.cancel([uq.Order(str(i), f"m{i}", "bid", uq.BUY_YES, 0.45, 100.0, LATER) for i in range(21)])
    assert [len(x["json"]["orders"]) for x in s.sent] == [20, 1] and s.sent[0]["json"]["orders"][0] == {"orderId": "0", "marketSlug": "m0"}
    s.sent.clear()
    b.cancel_all([])
    assert s.sent == []                                                                                  # an empty list would cancel everything: refused
    b.cancel_all(["m1", "m2"])
    assert s.sent == [{"method": "POST", "path": "/v1/orders/open/cancel", "json": {"slugs": ["m1", "m2"]}, "params": None, "headers": s.sent[0]["headers"]}]


def test_open_orders_are_read_for_our_markets_only():
    payload = {"orders": [
        {"id": "a1", "marketSlug": "m1", "intent": "ORDER_INTENT_BUY_LONG", "price": {"value": "0.45"}, "quantity": 100, "leavesQuantity": 70, "goodTillTime": "2026-11-12T15:03:00Z"},
        {"id": "a2", "marketSlug": "m1", "intent": "ORDER_INTENT_BUY_SHORT", "price": {"value": "0.47"}, "quantity": 100, "goodTillTime": "2026-11-12T15:03:00Z"},
        {"id": "a3", "marketSlug": "m1", "intent": "ORDER_INTENT_SELL_SHORT", "price": {"value": "0.44"}, "quantity": 30, "leavesQuantity": 30},
        {"id": "zz", "marketSlug": "somebody-elses-market", "intent": "ORDER_INTENT_BUY_LONG", "price": {"value": "0.10"}, "quantity": 5}]}
    s = Session({"/v1/orders/open": [Resp(200, payload)]})
    orders = broker(s).open_orders(["m1"])
    assert [(o.id, o.side, o.price, o.qty) for o in orders] == [("a1", "bid", 0.45, 70.0), ("a2", "ask", 0.47, 100.0), ("a3", "bid", 0.44, 30.0)]
    assert orders[0].expires == pytest.approx(1794495780.0) and orders[2].expires == 0.0
    assert s.sent[0]["method"] == "GET" and s.sent[0]["json"] is None


def test_positions_are_read_page_by_page_and_bounded_at_a_dollar_a_contract():
    first = {"positions": {"m1": {"qtyBoughtDecimal": "60", "qtySoldDecimal": "0"}, "old": {"qtyBoughtDecimal": "5", "qtySoldDecimal": "0", "expired": True}},
             "nextCursor": "c2", "eof": False}
    second = {"positions": {"m2": {"qtyBoughtDecimal": "10", "qtySoldDecimal": "100"}}, "eof": True}
    s = Session({"/v1/portfolio/positions": [Resp(200, first), Resp(200, second)]})
    pos = broker(s).positions()
    assert set(pos) == {"m1", "m2"} and pos["m1"].bought == 60 and pos["m2"].net == -90
    assert pos["m1"].at_risk() == 60 and pos["m2"].at_risk() == 90
    assert [x["params"] for x in s.sent] == [None, {"cursor": "c2"}]


def test_reading_is_retried_and_the_account_value_is_read_from_the_balances():
    s = Session({"/v1/account/balances": [Resp(503, "busy"), Resp(200, {"balances": [{"currency": "USD", "buyingPower": 400.0, "assetNotional": 55.5}]})]})
    assert broker(s).equity({}) == pytest.approx(455.5) and len(s.sent) == 2
    assert broker(Session({"/v1/account/balances": [Resp(200, {"balances": []})]})).equity({}) is None


def test_earnings_are_asked_for_by_date():
    s = Session({"/v1/incentives/earnings": [Resp(200, {"rewards": [{"reward": 1.31, "marketSlug": "m1", "date": "2026-11-12", "status": "PAID"}]})]})
    rows = broker(s).earnings("2026-11-12")
    assert rows[0]["reward"] == 1.31 and s.sent[0]["params"] == {"start_date": "2026-11-12", "program_type": "liquidityProgram"}

"""The live broker cannot be run against the exchange here, so these tests
check (a) the gates that keep it off and (b) the adapter logic against a
stand-in client that returns the SDK's own response types."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from kht.trading.live import ENABLE_ENV, ENABLE_VALUE, LiveBroker, LiveTradingNotPermitted, preflight
from kht.trading.models import Intent, MarketInfo, OrderKind, OrderStatus, Side
from kht.trading.portfolio import Portfolio

M = MarketInfo(1, "0xc", "Q?", "T0", "T1", "Yes", "No", fee_rate=0.04, tick=0.01)
GOOD_ENV = {ENABLE_ENV: ENABLE_VALUE, "POLYMARKET_PRIVATE_KEY": "k", "POLYMARKET_WALLET_ADDRESS": "0xw"}


class Geo:
    def __init__(self, blocked):
        self.blocked = blocked

    def geoblock(self):
        return {"blocked": self.blocked, "country": "US", "region": "OH"}


def test_preflight_refuses_without_explicit_opt_in():
    with pytest.raises(LiveTradingNotPermitted, match="live trading is off"):
        preflight(Geo(False), env={})


def test_preflight_refuses_without_credentials():
    with pytest.raises(LiveTradingNotPermitted, match="missing credential"):
        preflight(Geo(False), env={ENABLE_ENV: ENABLE_VALUE})


def test_preflight_refuses_in_a_blocked_location():
    with pytest.raises(LiveTradingNotPermitted, match="does not accept orders"):
        preflight(Geo(True), env=GOOD_ENV)


def test_preflight_passes_only_when_everything_holds():
    preflight(Geo(False), env=GOOD_ENV)


def test_sdk_response_types_match_what_the_adapter_reads():
    """Guards against an SDK upgrade silently renaming fields the adapter depends on."""
    acct = pytest.importorskip("polymarket.models.clob.account")
    resp = pytest.importorskip("polymarket.models.clob.order_response")
    assert {"ok", "order_id", "status", "making_amount", "taking_amount"} <= set(resp.AcceptedOrder.model_fields)
    assert {"ok", "code", "message"} <= set(resp.RejectedOrder.model_fields)
    assert {"size_matched", "status", "price"} <= set(acct.OpenOrder.model_fields)
    assert "balance" in acct.BalanceAllowance.model_fields
    from polymarket import SecureClient
    for name in ("place_limit_order", "place_market_order", "cancel_order", "cancel_all", "get_order",
                 "get_closed_only_mode", "get_balance_allowance"):
        assert hasattr(SecureClient, name)


class FakeClient:
    def __init__(self, closed_only=False):
        self.closed_only = closed_only
        self.calls = []
        self.next = None
        self.remote = {}

    def get_closed_only_mode(self):
        return self.closed_only

    def place_limit_order(self, **kw):
        self.calls.append(("limit", kw))
        return self.next

    def place_market_order(self, **kw):
        self.calls.append(("market", kw))
        return self.next

    def cancel_order(self, order_id):
        self.calls.append(("cancel", order_id))

    def get_order(self, order_id):
        return self.remote[order_id]

    def get_balance_allowance(self, asset_type):
        return SimpleNamespace(balance=123_450_000, allowances={})


def accepted(status, making="0", taking="0", oid="0xabc"):
    return SimpleNamespace(ok=True, order_id=oid, status=status, making_amount=Decimal(making), taking_amount=Decimal(taking))


def test_closed_only_account_is_refused():
    with pytest.raises(LiveTradingNotPermitted):
        LiveBroker(FakeClient(closed_only=True), Portfolio(100))


def test_taker_buy_sends_fill_and_kill_with_price_cap_and_books_the_fill():
    c = FakeClient(); br = LiveBroker(c, Portfolio(100.0))
    c.next = accepted("matched", making="18.60", taking="20")        # paid $18.60 for 20 shares
    o, fills = br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.TAKER, 0.93, 20), M, now=1000)
    kind, kw = c.calls[0]
    assert kind == "market" and kw["order_type"] == "FAK" and kw["max_price"] == "0.93" and kw["amount"] == "18.6"
    assert o.status == OrderStatus.FILLED and fills[0].size == 20 and fills[0].price == pytest.approx(0.93)
    assert fills[0].fee == pytest.approx(20 * 0.04 * 0.93 * 0.07)
    assert br.portfolio.shares("T0") == 20


def test_maker_order_is_post_only_and_fills_arrive_through_sync():
    c = FakeClient(); br = LiveBroker(c, Portfolio(100.0))
    c.next = accepted("live", oid="0x1")
    o, fills = br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.92, 20, expires_ts=5000), M, now=1000)
    kind, kw = c.calls[0]
    assert kind == "limit" and kw["post_only"] is True and kw["expiration"] == 5000
    assert o.status == OrderStatus.OPEN and not fills
    c.remote["0x1"] = SimpleNamespace(size_matched=Decimal("5"), status="LIVE")
    f = br.sync({1: M}, now=1100)
    assert len(f) == 1 and f[0].size == 5 and f[0].fee == 0 and f[0].maker
    c.remote["0x1"] = SimpleNamespace(size_matched=Decimal("20"), status="MATCHED")
    f = br.sync({1: M}, now=1200)
    assert f[0].size == 15 and o.status == OrderStatus.FILLED
    assert br.portfolio.shares("T0") == 20 and br.portfolio.cash == pytest.approx(100 - 18.4)


def test_exchange_rejection_books_nothing():
    c = FakeClient(); br = LiveBroker(c, Portfolio(100.0))
    c.next = SimpleNamespace(ok=False, code="not_enough_balance", message="insufficient")
    o, fills = br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.TAKER, 0.93, 20), M, now=1000)
    assert o.status == OrderStatus.REJECTED and "not_enough_balance" in o.reason and not fills
    assert br.portfolio.cash == 100.0 and not br.orders


def test_last_line_order_size_cap():
    c = FakeClient(); br = LiveBroker(c, Portfolio(1000.0), max_order_usd=25)
    o, _ = br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.TAKER, 0.93, 100), M, now=1000)
    assert o.status == OrderStatus.REJECTED and not c.calls        # never reached the exchange


def test_cash_on_exchange_converts_from_base_units():
    assert LiveBroker(FakeClient(), Portfolio(0)).cash_on_exchange() == pytest.approx(123.45)

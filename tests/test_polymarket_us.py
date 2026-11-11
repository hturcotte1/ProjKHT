import json

import pytest

from kht.api.polymarket_us import GATEWAY, PolymarketUS, taker_fee_per_share, yes_settlement


class FakeHttp:
    """Serves canned pages and records what was asked for."""

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def get(self, url, params=None, **kw):
        self.calls.append((url, dict(params or {})))
        if url.endswith("/v1/markets"):
            return {"markets": self.pages.get(params["offset"], [])}
        if url.endswith("/v1/price-history"):
            return {"history": [{"timestamp": "100", "longPrice": 0.97, "shortPrice": 0.05}, {"timestamp": 200, "longPrice": "bad"}]}
        if url.endswith("/settlement"):
            return {"slug": "x", "settlement": 1}
        return {}


def test_a_short_page_does_not_end_the_listing_only_an_empty_one_does():
    full = [{"id": i} for i in range(500)]
    short = [{"id": 500 + i} for i in range(499)]          # the gateway drops a hidden row after cutting the page
    http = FakeHttp({0: full, 500: short, 1000: [{"id": 2000}], 1500: []})
    got = list(PolymarketUS(http).iter_markets(closed=True, categories="sports"))
    assert len(got) == 1000
    assert [c[1]["offset"] for c in http.calls] == [0, 500, 1000, 1500]
    assert http.calls[0][1]["closed"] == "true" and http.calls[0][1]["categories"] == "sports"


def test_price_history_keeps_well_formed_points_as_yes_ask_and_no_ask():
    pm = PolymarketUS(FakeHttp({}))
    assert pm.price_history("some-market") == [(100, 0.97, 0.05)]
    assert pm.settlement("some-market") == 1.0


def test_taker_fee_is_largest_in_the_middle_and_small_near_certainty():
    assert taker_fee_per_share(0.50) == pytest.approx(0.02375)
    assert taker_fee_per_share(0.96) == pytest.approx(0.003648)
    assert taker_fee_per_share(0.96, theta=0.0695) == pytest.approx(0.0026688)


def test_yes_settlement_reads_the_first_outcome_price_of_a_resolved_market_only():
    assert yes_settlement({"status": "MARKET_STATUS_RESOLVED", "outcomePrices": json.dumps(["1", "0"])}) == 1.0
    assert yes_settlement({"status": "MARKET_STATUS_RESOLVED", "outcomePrices": ["0", "1"]}) == 0.0
    assert yes_settlement({"status": "MARKET_STATUS_OPEN", "outcomePrices": json.dumps(["0.15", "0.85"])}) is None
    assert yes_settlement({"status": "MARKET_STATUS_RESOLVED", "outcomePrices": "not json"}) is None
    assert GATEWAY.startswith("https://")

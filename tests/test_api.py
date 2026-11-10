"""API-client behaviour that has bitten us before, pinned with a fake transport."""

import pytest

from kht.api.polymarket import Polymarket, best_bid_ask, parse_json_list


class FakeHttp:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def get(self, url, params=None, **kw):
        self.calls.append((url, dict(params or {})))
        return self.pages[len(self.calls) - 1]


def test_trade_pagination_resends_the_market_filter():
    """A cursor on its own continues through the *global* feed, so every page
    request must repeat the condition filter."""
    pages = [
        {"data": [{"condition_id": "0xabc", "timestamp": 2}], "pagination": {"has_more": True, "next_cursor": "c1"}},
        {"data": [{"condition_id": "0xabc", "timestamp": 1}], "pagination": {"has_more": False, "next_cursor": None}},
    ]
    http = FakeHttp(pages)
    trades = list(Polymarket(http).iter_trades(condition="0xabc"))
    assert len(trades) == 2
    assert all(call[1].get("condition") == "0xabc" for call in http.calls)
    assert http.calls[1][1]["cursor"] == "c1"


def test_trade_pagination_refuses_rows_from_other_markets():
    pages = [{"data": [{"condition_id": "0xOTHER", "timestamp": 2}], "pagination": {"has_more": False}}]
    with pytest.raises(RuntimeError):
        list(Polymarket(FakeHttp(pages)).iter_trades(condition="0xabc"))


def test_price_history_follows_cursor_with_token():
    pages = [
        {"data": [{"timestamp": 10, "price": 0.4}], "pagination": {"has_more": True, "next_cursor": "n"}},
        {"data": [{"timestamp": 20, "price": 0.5}], "pagination": {"has_more": False}},
    ]
    http = FakeHttp(pages)
    pts = Polymarket(http).prices_history("tok", interval="max", bucket_seconds=10_800)
    assert pts == [(10, 0.4), (20, 0.5)]
    assert http.calls[1][1]["token_id"] == "tok" and http.calls[1][1]["cursor"] == "n"


def test_best_bid_ask_does_not_depend_on_level_order():
    book = {"bids": [{"price": "0.40", "size": "10"}, {"price": "0.45", "size": "7"}],
            "asks": [{"price": "0.60", "size": "3"}, {"price": "0.47", "size": "9"}]}
    assert best_bid_ask(book) == (0.45, 0.47, 7.0, 9.0)
    assert best_bid_ask({"bids": [], "asks": []}) == (None, None, 0.0, 0.0)


def test_parse_json_list_handles_gamma_encodings():
    assert parse_json_list('["Yes", "No"]') == ["Yes", "No"]
    assert parse_json_list(["a"]) == ["a"]
    assert parse_json_list(None) == []
    assert parse_json_list("not json") == []

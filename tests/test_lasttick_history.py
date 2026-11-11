"""Test L1 on the history of settled markets (scripts/lasttick_history.py, docs/11 section 5, item 3)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("lasttick_history", Path(__file__).resolve().parents[1] / "scripts" / "lasttick_history.py")
lh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lh)

END = float(pd.Timestamp("2026-11-10 22:00:00").timestamp())
REACH = {"btc": {h: 0.03 for h in range(1, 31)}}


def points(book_at_quarter, later=None):
    """Stored minute points: the one labelled a minute before a moment holds the book at that moment."""
    pts = [[END - 960, *book_at_quarter]]
    for seconds, (yes, no) in (later or {}).items():
        pts.append([END - seconds - 60, yes, no])
    return sorted(pts)


def market(slug, strike, yes_settle, quotes, **kw):
    row = {"slug": slug, "kind": "above_below", "horizon": "daily", "coin": "btc", "end": END, "strike": strike, "lower": np.nan, "upper": np.nan,
           "direction": "unspecified", "price_to_beat": np.nan, "yes_settle": yes_settle, "closed_at": "2026-11-10T22:00:20Z", "quotes": json.dumps(quotes), "traded": 0.0}
    row.update(kw)
    return row


def test_a_stored_point_is_the_book_a_minute_after_its_label():
    pts = [[END - 960, 0.02, 0.99], [END - 900, 0.05, 0.99]]
    assert lh.stored_book(pts, END - 900) == {"bid1": 0.01, "bid_qty1": 1.0, "ask1": 0.02, "ask_qty1": 1.0}
    assert lh.stored_book(pts, END - 840)["ask1"] == 0.05
    assert lh.stored_book(pts, END - 600) is None                                  # nothing stored for that minute
    assert lh.stored_book([[END - 960, 0.03, 0.97]], END - 900) is None             # no spread: one side was empty and the last trade stands in for it
    assert lh.stored_book([[END - 960, 0.02, 0.90]], END - 900) is None             # the same, with a last trade above the offer
    top = lh.stored_book([[END - 960, 1.0, 0.03]], END - 900)                       # nobody offering at any price
    assert top["ask1"] is None and top["bid1"] == 0.97


def test_the_slug_of_the_market_that_carries_the_index():
    assert lh.quarter_slug("btc", END - 900) == "cpc-btc-updown-15m-2026-11-10-2145z"
    assert lh.quarter_slug("xrp", END - 900) == "cpcxrp-xrp-updown-15m-2026-11-10-2145z"


def test_the_brake_is_fed_from_minute_prices():
    t = np.arange(int(END) - 7200, int(END), 60)
    closes = {"btc": pd.Series(74_000.0 + (t - t[0]) / 600.0, index=t)}             # the close of the minute starting at t
    h = lh.brake_history(closes, "btc", END - 900)
    assert [a for a, _ in h] == list(np.arange(END - 900 - 3900, END - 900 + 1, 300))
    assert h[-1] == (END - 900, closes["btc"].loc[int(END) - 960])                  # the level at a mark is the close of the minute ending there
    assert lh.brake_history(closes, "eth", END - 900) == []


def test_the_rule_on_history_one_reading_a_market():
    far = market("far", 78_000, 0.0, points((0.02, 0.99), {600: (0.02, 0.99), 300: (0.02, 0.99), 120: (0.03, 1.0)}))
    lost = market("lost", 77_000, 1.0, points((0.02, 0.99)))                        # out of reach, and it came in
    near = market("near", 74_500, 0.0, points((0.02, 0.99)))
    empty = market("empty", 79_000, 0.0, points((0.03, 0.97)))                      # out of reach, but the stored price is not a book
    silent = market("silent", 80_000, 0.0, [])
    deep = market("deep", 70_000, 1.0, points((0.99, 0.03)))
    hit = market("hit", 80_000, 1.0, [], kind="one_touch", direction="up", closed_at="2026-11-08T15:05:20Z")
    f = pd.DataFrame([far, lost, near, empty, silent, deep, hit])
    idx = pd.Series({("btc", END - 900): 74_000.0})
    idx.index = pd.MultiIndex.from_tuples(idx.index, names=["coin", "at"])
    res = lh.score(f, idx, REACH, None, {}).set_index("slug")
    assert res["fate"].to_dict() == {"far": "trade", "lost": "trade", "near": "within reach", "empty": "out of reach, no real book stored",
                                     "silent": "out of reach, no quote stored at all", "deep": "trade", "hit": "settled before its last quarter of an hour"}
    assert res.loc["far", "side"] == "sell" and res.loc["far", "pnl"] == pytest.approx(0.01 - 0.095 * 0.01 * 0.99)
    assert res.loc["lost", "pnl"] == pytest.approx(-0.99 - 0.095 * 0.01 * 0.99)
    assert res.loc["deep", "side"] == "buy" and res.loc["deep", "pnl"] == pytest.approx(0.01 - 0.095 * 0.99 * 0.01)
    assert bool(res.loc["far", "still_10m"]) and bool(res.loc["far", "still_5m"]) and not bool(res.loc["far", "still_2m"])
    # every result that was out of reach is counted, with or without an order to trade against
    oor = res[res["out_of_reach"] == True]  # noqa: E712
    assert set(oor.index) == {"far", "lost", "empty", "silent", "deep"} and oor["held"].to_dict() == {"far": True, "lost": False, "empty": True, "silent": True, "deep": True}
    text = "\n".join(lh.describe("a yardstick", res.reset_index()))
    assert "out of reach by the rule, whatever the book showed: 5; of these the result changed in 1" in text and "trades (an order to trade against was stored at that moment): 3; lost 1" in text


def test_with_the_brake_a_fast_hour_is_not_traded_and_not_counted():
    far = market("far", 78_000, 0.0, points((0.02, 0.99)))
    idx = pd.Series({("btc", END - 900): 74_000.0})
    idx.index = pd.MultiIndex.from_tuples(idx.index, names=["coin", "at"])
    t = np.arange(int(END) - 7200, int(END), 60)
    calm = {"btc": pd.Series(74_000.0, index=t)}
    storm = {"btc": pd.Series(np.where(t < END - 2400, 76_000.0, 74_000.0), index=t)}
    f = pd.DataFrame([far])
    assert lh.score(f, idx, REACH, {"btc": 0.0105}, calm).loc[0, "fate"] == "trade"
    res = lh.score(f, idx, REACH, {"btc": 0.0105}, storm)
    assert res.loc[0, "fate"] == "out of reach, but the index has been moving fast" and not (res["out_of_reach"] == True).any()  # noqa: E712
    assert lh.score(f, idx, REACH, {"btc": 0.0105}, {}).loc[0, "fate"] == "out of reach, too little index history"

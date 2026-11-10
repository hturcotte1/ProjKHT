"""Tape -> quote panel. Every research conclusion rests on these mappings."""

import numpy as np
import pandas as pd
import pytest

from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes, tape_mids

DAY = 86_400


def tape(rows):
    """rows: (market, ts, p0, dir0, size, cum_before)"""
    df = pd.DataFrame(rows, columns=["market_id", "ts", "p0", "dir0", "size", "cum_before"])
    df["usd"] = df["p0"] * df["size"]
    return df


def meta(winner=0.0, final0=1.0, category="politics"):
    return pd.DataFrame([{"market_id": 1, "winner": winner, "final0": final0, "event_id": 9, "category": category,
                          "end_ts": 20 * DAY, "closed_ts": 18 * DAY, "start_ts": 0.0, "neg_risk": False}])


def test_last_buy_marks_the_ask_and_last_sell_marks_the_bid():
    t = tape([
        (1, 10 * DAY + 100, 0.60, +1, 10, 200_000),     # taker bought outcome 0 at 0.60
        (1, 10 * DAY + 200, 0.58, -1, 10, 200_010),     # taker sold it at 0.58
        (1, 10 * DAY + 300, 0.61, +1, 10, 200_020),     # later buy at 0.61 -> the ask
        (1, 10 * DAY + 400, 0.59, -1, 10, 200_030),     # later sell at 0.59 -> the bid
    ])
    q = period_quotes(t)
    assert len(q) == 1
    r = q.iloc[0]
    assert (r["ask0"], r["bid0"]) == (pytest.approx(0.61), pytest.approx(0.59))
    assert (r["ask0_first"], r["bid0_first"]) == (pytest.approx(0.60), pytest.approx(0.58))
    assert r["ts"] == 11 * DAY                           # stamped at the period's end
    assert r["vol"] == 40 and r["buy_n"] == 2 and r["sell_n"] == 2


def test_trades_before_the_volume_threshold_are_invisible():
    t = tape([(1, 10 * DAY + 100, 0.60, +1, 10, 50_000),      # market had not traded 100k yet
              (1, 11 * DAY + 100, 0.70, +1, 10, 150_000)])
    q = period_quotes(t, min_cum=100_000)
    assert list(q["period"]) == [11]


def test_other_side_is_the_mirror_image():
    t = tape([(1, 10 * DAY + 100, 0.93, +1, 10, 200_000),     # buy outcome 0 at 0.93
              (1, 10 * DAY + 200, 0.92, -1, 10, 200_010)])    # sell outcome 0 at 0.92 == buy outcome 1 at 0.08
    s = by_side(period_quotes(t), meta(winner=0.0)).set_index("side")
    assert s.loc[0, "ask"] == pytest.approx(0.93) and s.loc[0, "bid"] == pytest.approx(0.92)
    assert s.loc[1, "ask"] == pytest.approx(0.08) and s.loc[1, "bid"] == pytest.approx(0.07)
    assert s.loc[0, "won"] == 1.0 and s.loc[1, "won"] == 0.0
    assert s.loc[0, "ask"] + s.loc[1, "bid"] == pytest.approx(1.0)
    # the lowest price at which outcome 1 was sold is one minus the highest price outcome 0 was bought
    assert s.loc[1, "bid_lo"] == pytest.approx(1 - 0.93)
    assert s.loc[0, "days_to_end"] == pytest.approx(20 - 11)


def test_split_resolution_is_a_half_payout_for_both_sides():
    t = tape([(1, 10 * DAY + 100, 0.93, +1, 10, 200_000), (1, 10 * DAY + 200, 0.92, -1, 10, 200_010)])
    s = by_side(period_quotes(t), meta(winner=np.nan, final0=0.5))
    assert list(s["won"]) == [0.5, 0.5]


def test_buy_at_ask_pnl_charges_todays_fee_for_the_category():
    t = tape([(1, 10 * DAY + 100, 0.93, +1, 10, 200_000), (1, 10 * DAY + 200, 0.92, -1, 10, 200_010)])
    s = add_taker_buy_pnl(by_side(period_quotes(t), meta(winner=0.0))).set_index("side")
    fee = 0.04 * 0.93 * 0.07                                  # politics rate
    assert s.loc[0, "net_ps"] == pytest.approx(1 - 0.93 - fee)
    assert s.loc[1, "net_ps"] == pytest.approx(0 - 0.08 - 0.04 * 0.08 * 0.92)
    free = add_taker_buy_pnl(by_side(period_quotes(t), meta(winner=0.0, category="geopolitics"))).set_index("side")
    assert free.loc[0, "fee_ps"] == 0.0                       # geopolitics is fee-free


def test_tape_mid_falls_back_to_last_trade_when_one_side_is_missing():
    t = tape([(1, 10 * DAY + 100, 0.60, +1, 10, 200_000)])    # only a buy printed
    m = tape_mids(period_quotes(t))
    assert m.iloc[0]["price"] == pytest.approx(0.60)
    both = tape([(1, 10 * DAY + 100, 0.60, +1, 10, 200_000), (1, 10 * DAY + 200, 0.58, -1, 10, 200_010)])
    assert tape_mids(period_quotes(both)).iloc[0]["price"] == pytest.approx(0.59)


def test_chunked_processing_gives_the_same_panel():
    rng = np.random.default_rng(0)
    rows = []
    for market in range(1, 41):
        cum = 150_000.0
        for k in range(60):
            rows.append((market, 10 * DAY + k * 7_000, float(rng.uniform(0.2, 0.8)), int(rng.choice([-1, 1])), 10.0, cum))
            cum += 10
    t = tape(rows)
    whole = period_quotes(t, chunk_rows=10**9)
    chunked = period_quotes(t, chunk_rows=97)          # forces many chunks, none splitting a market
    pd.testing.assert_frame_equal(whole, chunked)

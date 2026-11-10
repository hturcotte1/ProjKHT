"""The backtester must not peek, must charge fees, and must respect capital."""

import numpy as np
import pandas as pd
import pytest

from kht.backtest.harvest import Capital, Rule, candidate_trades, prepare, run_portfolio

DAY = 86_400


def panel(rows):
    """rows: (market, side, period, ask, bid, ask_first, bid_first, won, closed_period, dte, cluster)"""
    cols = ["market_id", "side", "period", "ask", "bid", "ask_first", "bid_first", "won", "closed_p", "days_to_end", "cluster"]
    df = pd.DataFrame(rows, columns=cols)
    df["ts"] = (df["period"] + 1) * DAY
    df["closed_ts"] = df["closed_p"] * DAY + 10
    df["usd"] = 1_000.0
    df["fee_rate"] = 0.04
    df["category"] = "politics"
    return prepare(df)


def test_entry_uses_next_periods_first_print_not_the_signal_bar():
    # signal on period 10 (ask 0.93). Period 11 opens at 0.95: that is the fill.
    s = panel([
        (1, 0, 10, 0.93, 0.92, 0.90, 0.89, 1.0, 20, 9.0, 5),
        (1, 0, 11, 0.94, 0.93, 0.95, 0.94, 1.0, 20, 8.0, 5),
    ])
    t = candidate_trades(s, Rule(ask_lo=0.90, ask_hi=0.97, dte_lo=3, dte_hi=60))
    assert len(t) == 1
    assert t.loc[0, "entry_px"] == 0.95 and t.loc[0, "entry_period"] == 11
    assert t.loc[0, "entry_fee"] == pytest.approx(0.04 * 0.95 * 0.05)
    assert t.loc[0, "pnl_ps"] == pytest.approx(1.0 - 0.95 - 0.04 * 0.95 * 0.05)
    assert t.loc[0, "exit_period"] == 20


def test_no_trade_when_price_has_left_the_range_or_no_print_arrives():
    gone = panel([
        (1, 0, 10, 0.93, 0.92, 0.93, 0.92, 1.0, 20, 9.0, 5),
        (1, 0, 11, 0.99, 0.98, 0.99, 0.98, 1.0, 20, 8.0, 5),      # jumped above the limit
    ])
    assert candidate_trades(gone, Rule()).empty
    late = panel([
        (1, 0, 10, 0.93, 0.92, 0.93, 0.92, 1.0, 20, 9.0, 5),
        (1, 0, 15, 0.93, 0.92, 0.93, 0.92, 1.0, 20, 4.0, 5),      # next print 5 periods later
    ])
    assert candidate_trades(late, Rule(max_wait=3, dte_lo=5)).empty


def test_last_bar_signal_cannot_trade():
    s = panel([(1, 0, 10, 0.93, 0.92, 0.93, 0.92, 1.0, 20, 9.0, 5)])
    assert candidate_trades(s, Rule()).empty


def test_losing_trade_loses_the_full_cost():
    s = panel([
        (1, 0, 10, 0.93, 0.92, 0.93, 0.92, 0.0, 20, 9.0, 5),
        (1, 0, 11, 0.93, 0.92, 0.93, 0.92, 0.0, 20, 8.0, 5),
    ])
    t = candidate_trades(s, Rule())
    assert t.loc[0, "pnl_ps"] == pytest.approx(-(0.93 + 0.04 * 0.93 * 0.07))


def test_time_exit_sells_at_a_later_bid_print_and_pays_fee():
    s = panel([
        (1, 0, 10, 0.93, 0.92, 0.93, 0.92, 1.0, 30, 9.0, 5),
        (1, 0, 11, 0.94, 0.93, 0.93, 0.92, 1.0, 30, 8.0, 5),      # entry here at 0.93
        (1, 0, 12, 0.96, 0.95, 0.95, 0.94, 1.0, 30, 2.0, 5),      # dte <= 3 -> trigger
        (1, 0, 13, 0.97, 0.96, 0.97, 0.96, 1.0, 30, 1.0, 5),      # sell at first bid print: 0.96
    ])
    t = candidate_trades(s, Rule(exit_dte=3.0))
    assert t.loc[0, "exit_reason"] == "time" and t.loc[0, "exit_period"] == 13
    assert t.loc[0, "proceeds"] == pytest.approx(0.96 - 0.04 * 0.96 * 0.04)


def test_one_trade_per_market_even_if_it_qualifies_again():
    rows = [(1, 0, p, 0.93, 0.92, 0.93, 0.92, 1.0, 40, 30.0 - p, 5) for p in range(10, 20)]
    assert len(candidate_trades(panel(rows), Rule())) == 1


def _two_trades(cluster_b=6):
    return panel([
        (1, 0, 10, 0.93, 0.92, 0.93, 0.92, 1.0, 20, 9.0, 5),
        (1, 0, 11, 0.93, 0.92, 0.93, 0.92, 1.0, 20, 8.0, 5),
        (2, 0, 10, 0.93, 0.92, 0.93, 0.92, 0.0, 20, 9.0, cluster_b),
        (2, 0, 11, 0.93, 0.92, 0.93, 0.92, 0.0, 20, 8.0, cluster_b),
    ])


def test_portfolio_equity_matches_trade_pnl():
    t = candidate_trades(_two_trades(), Rule())
    res = run_portfolio(t, Capital(bankroll=1000, stake=20, max_event=40))
    assert len(res.trades) == 2
    assert res.equity["equity"].iloc[-1] == pytest.approx(1000 + res.trades["pnl"].sum())
    assert res.trades["stake"].max() == pytest.approx(20)
    # one winner (+~1.4) and one total loss (-20)
    assert res.trades["pnl"].min() == pytest.approx(-20)


def test_event_cap_limits_correlated_bets():
    t = candidate_trades(_two_trades(cluster_b=5), Rule())      # same event
    res = run_portfolio(t, Capital(bankroll=1000, stake=20, max_event=25))
    assert res.trades["stake"].sum() <= 25 + 1e-9


def test_cannot_spend_more_than_cash():
    t = candidate_trades(_two_trades(), Rule())
    res = run_portfolio(t, Capital(bankroll=30, stake=20, max_event=40, max_exposure_frac=1.0))
    assert res.trades["stake"].sum() <= 30 + 1e-9
    assert res.equity["cash"].min() >= -1e-9

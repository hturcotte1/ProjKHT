"""Reconstruct tradable quotes from the trade tape.

Polymarket publishes no historical order books, but every tape row is a taker
order with a known direction, so the tape itself says what could be traded:

* the last taker **buy** of an outcome printed at (about) its **ask**;
* the last taker **sell** printed at (about) its **bid**.

Aggregating by market and period gives, for outcome 0, ``ask0`` / ``bid0``
(and by mirror symmetry ``ask1 = 1 - bid0``, ``bid1 = 1 - ask0``), plus the
flow that went through. A backtest that buys at ``ask`` is then buying at a
price someone demonstrably paid, not at a hypothetical mid.

The panel is "long by side": two rows per market-period, one per outcome, so
that 'buy the 93c side' is one filter instead of two mirrored cases.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Fee rates per share = rate * p * (1 - p), by category, from
# https://docs.polymarket.com/trading/fees (checked 2026-11-10). Historical
# markets often traded fee-free; evaluating them at today's schedule is the
# conservative choice for a strategy that will trade today.
CURRENT_FEE_RATE = {
    "crypto": 0.07, "sports": 0.05, "finance": 0.04, "politics": 0.04, "economics": 0.05,
    "culture": 0.05, "weather": 0.05, "other": 0.05, "mentions": 0.04, "tech": 0.04, "geopolitics": 0.0,
}


def period_quotes(tr: pd.DataFrame, period_seconds: int = 86_400, min_cum: float = 100_000) -> pd.DataFrame:
    """One row per (market, period) with end-of-period quote proxies and flow.

    Only trades made after the market had already traded ``min_cum`` shares are
    used (ex-ante universe; see ``sports.build_trades_table``).
    """
    t = tr[tr["cum_before"] >= min_cum]
    period = (t["ts"].to_numpy() // period_seconds).astype(np.int64)
    key = [t["market_id"].to_numpy(), period]
    buys = t["dir0"].to_numpy() > 0
    p0 = t["p0"].to_numpy(dtype=np.float64)
    size = t["size"].to_numpy(dtype=np.float64)
    usd = t["usd"].to_numpy(dtype=np.float64)
    df = pd.DataFrame({
        "market_id": key[0], "period": key[1], "ts": t["ts"].to_numpy(),
        "p0": p0, "size": size, "usd": usd,
        "ask_px": np.where(buys, p0, np.nan), "bid_px": np.where(~buys, p0, np.nan),
        "buy_sz": np.where(buys, size, 0.0), "sell_sz": np.where(~buys, size, 0.0),
        "buy_n": buys.astype(np.int32), "sell_n": (~buys).astype(np.int32),
        "small_buy_n": (buys & (usd < 50)).astype(np.int32), "small_sell_n": (~buys & (usd < 50)).astype(np.int32),
        "big_buy_usd": np.where(buys & (usd >= 1000), usd, 0.0), "big_sell_usd": np.where(~buys & (usd >= 1000), usd, 0.0),
    })
    g = df.groupby(["market_id", "period"], sort=True)
    out = g.agg(
        ask0=("ask_px", "last"), bid0=("bid_px", "last"), last0=("p0", "last"),
        ask0_first=("ask_px", "first"), bid0_first=("bid_px", "first"),
        ask0_lo=("ask_px", "min"), ask0_hi=("ask_px", "max"), bid0_lo=("bid_px", "min"), bid0_hi=("bid_px", "max"),
        vol=("size", "sum"), usd=("usd", "sum"), n=("size", "size"),
        buy_sz=("buy_sz", "sum"), sell_sz=("sell_sz", "sum"), buy_n=("buy_n", "sum"), sell_n=("sell_n", "sum"),
        small_buy_n=("small_buy_n", "sum"), small_sell_n=("small_sell_n", "sum"),
        big_buy_usd=("big_buy_usd", "sum"), big_sell_usd=("big_sell_usd", "sum"),
        last_ts=("ts", "last"),
    ).reset_index()
    out["ts"] = (out["period"] + 1) * period_seconds          # quotes are as of the period's end
    return out


def by_side(q: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Stack the panel so each row is one *outcome* in one market-period.

    ``ask`` is what a taker pays to buy this outcome, ``bid`` what a taker gets
    for selling it, ``won`` whether it paid out.
    """
    m = meta.set_index("market_id")
    win = m["winner"].reindex(q["market_id"]).to_numpy()
    # payoff of outcome 0: 1 or 0, or 0.5 for the rare split resolution
    final0 = m["final0"].reindex(q["market_id"]).to_numpy()
    pay0 = np.where(win == 0, 1.0, np.where(win == 1, 0.0, np.where(final0 == 0.5, 0.5, np.nan)))
    base = {
        "market_id": q["market_id"].to_numpy(), "period": q["period"].to_numpy(), "ts": q["ts"].to_numpy(),
        "vol": q["vol"].to_numpy(), "usd": q["usd"].to_numpy(), "n": q["n"].to_numpy(),
    }
    s0 = pd.DataFrame({
        **base, "side": 0, "ask": q["ask0"].to_numpy(), "bid": q["bid0"].to_numpy(), "last": q["last0"].to_numpy(),
        "ask_first": q["ask0_first"].to_numpy(), "bid_first": q["bid0_first"].to_numpy(),
        "ask_lo": q["ask0_lo"].to_numpy(), "ask_hi": q["ask0_hi"].to_numpy(),
        "bid_lo": q["bid0_lo"].to_numpy(), "bid_hi": q["bid0_hi"].to_numpy(),
        "buy_sz": q["buy_sz"].to_numpy(), "sell_sz": q["sell_sz"].to_numpy(),
        "buy_n": q["buy_n"].to_numpy(), "sell_n": q["sell_n"].to_numpy(),
        "small_buy_n": q["small_buy_n"].to_numpy(), "small_sell_n": q["small_sell_n"].to_numpy(),
        "big_buy_usd": q["big_buy_usd"].to_numpy(), "big_sell_usd": q["big_sell_usd"].to_numpy(),
        "won": pay0,
    })
    s1 = pd.DataFrame({
        **base, "side": 1, "ask": 1.0 - q["bid0"].to_numpy(), "bid": 1.0 - q["ask0"].to_numpy(),
        "last": 1.0 - q["last0"].to_numpy(),
        "ask_first": 1.0 - q["bid0_first"].to_numpy(), "bid_first": 1.0 - q["ask0_first"].to_numpy(),
        "ask_lo": 1.0 - q["bid0_hi"].to_numpy(), "ask_hi": 1.0 - q["bid0_lo"].to_numpy(),
        "bid_lo": 1.0 - q["ask0_hi"].to_numpy(), "bid_hi": 1.0 - q["ask0_lo"].to_numpy(),
        "buy_sz": q["sell_sz"].to_numpy(), "sell_sz": q["buy_sz"].to_numpy(),
        "buy_n": q["sell_n"].to_numpy(), "sell_n": q["buy_n"].to_numpy(),
        "small_buy_n": q["small_sell_n"].to_numpy(), "small_sell_n": q["small_buy_n"].to_numpy(),
        "big_buy_usd": q["big_sell_usd"].to_numpy(), "big_sell_usd": q["big_buy_usd"].to_numpy(),
        "won": 1.0 - pay0,
    })
    out = pd.concat([s0, s1], ignore_index=True)
    mid = out["market_id"]
    ev = m["event_id"].reindex(mid).to_numpy()
    out["cluster"] = np.where(ev >= 0, ev, -mid.to_numpy())
    out["category"] = m["category"].reindex(mid).to_numpy()
    out["end_ts"] = m["end_ts"].reindex(mid).to_numpy()
    out["closed_ts"] = m["closed_ts"].reindex(mid).to_numpy()
    out["start_ts"] = m["start_ts"].reindex(mid).to_numpy()
    out["neg_risk"] = m["neg_risk"].reindex(mid).to_numpy()
    out["days_to_end"] = (out["end_ts"] - out["ts"]) / 86_400          # scheduled: known in advance
    out["days_to_close"] = (out["closed_ts"] - out["ts"]) / 86_400     # realised: known only afterwards
    out["age_days"] = (out["ts"] - out["start_ts"]) / 86_400
    out["fee_rate"] = out["category"].map(CURRENT_FEE_RATE).fillna(0.05)
    out["day"] = out["ts"] // 86_400
    return out


def add_taker_buy_pnl(s: pd.DataFrame) -> pd.DataFrame:
    """Profit per share of buying this outcome at the ask and holding to
    resolution, before and after today's taker fee."""
    s = s.copy()
    s["fee_ps"] = s["fee_rate"] * s["ask"] * (1.0 - s["ask"])
    s["gross_ps"] = s["won"] - s["ask"]
    s["net_ps"] = s["gross_ps"] - s["fee_ps"]
    s["net_ret"] = s["net_ps"] / s["ask"]          # return on the cash put up
    return s

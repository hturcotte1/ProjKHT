"""Backtest of rule-based entries on the tape-derived quote panel.

Protocol (no look-ahead, no trading at the mid):

1. **Signal** at the end of period ``D`` from that period's closing quotes and
   from market facts known in advance (category, scheduled end date...).
2. **Entry** on a later period, at a price a taker demonstrably paid: the
   first taker-buy print of that outcome after the signal, provided it comes
   within ``max_wait`` periods and is still inside the price limits. If there
   is no such print the trade simply does not happen. Today's taker fee for
   the market's category is charged.
3. **Exit** by resolution (payoff 1 or 0), or by rule, at the first
   taker-sell print (the bid) after the rule triggers, again with the fee.
4. **Capital** is finite: trades are taken in time order subject to a stake
   size, a per-event cap, a cap on simultaneous exposure and available cash.

The output is a trade list plus a daily equity curve, so that the statistics
are those of an account, not of an average trade.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd


@dataclass
class Rule:
    """Entry/exit rule for one strategy variant."""

    ask_lo: float = 0.90
    ask_hi: float = 0.97
    dte_lo: float = 3.0              # scheduled days to end, lower bound
    dte_hi: float = 60.0
    categories: tuple[str, ...] | None = None
    min_period_usd: float = 0.0      # activity in the signal period
    max_wait: int = 3                # periods to wait for an entry print
    entry: str = "taker"             # "taker": lift the ask. "maker": rest a bid at the signal bar's bid
    exit_dte: float | None = None    # sell once scheduled days-to-end <= this (None = hold)
    stop_bid: float | None = None    # sell if the bid closes at or below this
    take_bid: float | None = None    # sell if the bid closes at or above this
    hold_periods: int | None = None  # sell after this many periods (None = no time limit)
    reentry: bool = False            # allow a new trade in the same market after the previous one exits
    name: str = "rule"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Capital:
    bankroll: float = 1_000.0
    stake: float = 20.0              # dollars per position
    max_event: float = 40.0          # dollars per event
    max_exposure_frac: float = 0.90  # of current equity
    compound: bool = False           # scale the stake with equity
    max_theme: float | None = None   # dollars per narrow topic tag (needs a "themes" column on the trades)


@dataclass
class Result:
    trades: pd.DataFrame
    equity: pd.DataFrame
    stats: dict = field(default_factory=dict)


def prepare(side_panel: pd.DataFrame) -> pd.DataFrame:
    """Sort the by-side panel and attach, to every row, the next rows' entry
    and exit prints of the same outcome (so entries never use the signal bar)."""
    s = side_panel.sort_values(["market_id", "side", "period"], kind="stable").reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    return s


def _series_index(s: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    series = s["series"].to_numpy()
    change = np.flatnonzero(np.diff(series)) + 1
    start = np.concatenate(([0], change))
    stop = np.concatenate((change, [len(series)]))
    return start, stop


def candidate_trades(
    s: pd.DataFrame, rule: Rule, period_seconds: int = 86_400, signal: np.ndarray | None = None
) -> pd.DataFrame:
    """All trades the rule would take with unlimited capital: at most one per
    market (the first time it qualifies) unless ``rule.reentry`` is set.

    ``signal`` optionally replaces the built-in price/duration filter with any
    boolean array aligned to ``s`` (it must only use information available at
    the end of each row's period). The price limits still apply to the entry.
    """
    period = s["period"].to_numpy()
    ask = s["ask"].to_numpy()
    bid = s["bid"].to_numpy()
    ask_first = s["ask_first"].to_numpy()
    bid_first = s["bid_first"].to_numpy()
    dte = s["days_to_end"].to_numpy()
    usd = s["usd"].to_numpy()
    fee_rate = s["fee_rate"].to_numpy()
    won = s["won"].to_numpy()
    closed_p = np.floor(s["closed_ts"].to_numpy() / float(period_seconds))

    bid_lo = s["bid_lo"].to_numpy()      # lowest price a taker sold this outcome at, per period
    if signal is None:
        signal = (ask > rule.ask_lo) & (ask <= rule.ask_hi) & (dte > rule.dte_lo) & (dte <= rule.dte_hi)
    else:
        signal = np.asarray(signal, dtype=bool) & (ask > rule.ask_lo) & (ask <= rule.ask_hi)
    if rule.entry == "maker":
        signal &= np.isfinite(bid)
    signal &= usd >= rule.min_period_usd
    if rule.categories is not None:
        signal &= s["category"].isin(rule.categories).to_numpy()

    start, stop = _series_index(s)
    rows = []
    market = s["market_id"].to_numpy()
    for a, b in zip(start, stop):
        sig = np.flatnonzero(signal[a:b])
        if len(sig) == 0:
            continue
        mid = int(market[a])
        busy_until = -1                    # row index of the previous trade's exit (re-entry mode)
        for i0 in sig:
            i = a + i0
            if i <= busy_until:
                continue
            entry = -1
            if rule.entry == "maker":
                # A bid resting at the signal bar's bid. It fills only when a
                # later taker sell prints strictly *through* it, which proves
                # the level was swept; a print merely at the price is ignored
                # because our place in the queue is unknown. Makers pay no fee.
                my_bid = float(bid[i])
                for j in range(i + 1, b):
                    if period[j] - period[i] > rule.max_wait:
                        break
                    if np.isfinite(bid_lo[j]) and bid_lo[j] < my_bid - 1e-9:
                        entry = j
                        break
                if entry < 0:
                    continue
                px_in, fee_in = my_bid, 0.0
            else:
                # first later row with a taker-buy print inside the limits
                for j in range(i + 1, b):
                    if period[j] - period[i] > rule.max_wait:
                        break
                    px = ask_first[j]
                    if np.isfinite(px):
                        if rule.ask_lo < px <= rule.ask_hi + 0.005:
                            entry = j
                        break                      # the first print decides: in range or no trade
                if entry < 0:
                    continue
                px_in = float(ask_first[entry])
                fee_in = float(fee_rate[entry] * px_in * (1 - px_in))
            # walk forward for a rule-based exit
            exit_row, exit_px, reason = -1, np.nan, "resolution"
            if (rule.exit_dte is not None or rule.stop_bid is not None or rule.take_bid is not None
                    or rule.hold_periods is not None):
                for j in range(entry, b - 1):
                    trig = None
                    if rule.hold_periods is not None and period[j] - period[entry] >= rule.hold_periods:
                        trig = "hold"
                    elif rule.exit_dte is not None and dte[j] <= rule.exit_dte:
                        trig = "time"
                    elif rule.stop_bid is not None and np.isfinite(bid[j]) and bid[j] <= rule.stop_bid:
                        trig = "stop"
                    elif rule.take_bid is not None and np.isfinite(bid[j]) and bid[j] >= rule.take_bid:
                        trig = "take"
                    if trig is None:
                        continue
                    # sell at the first taker-sell print after the trigger bar
                    for k in range(j + 1, b):
                        if np.isfinite(bid_first[k]):
                            exit_row, exit_px, reason = k, float(bid_first[k]), trig
                            break
                    break
            if exit_row >= 0:
                fee_out = float(fee_rate[exit_row] * exit_px * (1 - exit_px))
                exit_period = int(period[exit_row])
                proceeds = exit_px - fee_out
            else:
                if not np.isfinite(won[entry]):
                    continue
                exit_period = int(closed_p[entry])
                proceeds = float(won[entry])
                fee_out = 0.0
            rows.append((mid, int(s["side"].iloc[entry]), int(s["cluster"].iloc[entry]), s["category"].iloc[entry],
                         int(period[i]), int(period[entry]), max(exit_period, int(period[entry])), px_in, fee_in,
                         proceeds, reason, float(dte[i]), float(won[entry]) if np.isfinite(won[entry]) else np.nan))
            if rule.reentry:
                busy_until = exit_row if exit_row >= 0 else b
                continue
            break                          # this outcome's first trade; see the per-market step below
    cols = ["market_id", "side", "cluster", "category", "signal_period", "entry_period", "exit_period",
            "entry_px", "entry_fee", "proceeds", "exit_reason", "dte_at_signal", "won"]
    t = pd.DataFrame(rows, columns=cols)
    if t.empty:
        return t
    if not rule.reentry:
        # One position per market: whichever outcome signalled FIRST in time.
        # (Each outcome was scanned separately above. Preferring one outcome
        # over the other regardless of timing would need to know, at the first
        # signal, that the other side will qualify later: a look-ahead that
        # quietly drops trades in markets that went on to flip.)
        t = (t.sort_values(["signal_period", "entry_period", "side"])
              .drop_duplicates("market_id", keep="first"))
    t["cost"] = t["entry_px"] + t["entry_fee"]              # cash out per share
    t["pnl_ps"] = t["proceeds"] - t["cost"]
    t["ret"] = t["pnl_ps"] / t["cost"]
    t["hold"] = t["exit_period"] - t["entry_period"]
    return t.sort_values(["entry_period", "market_id"]).reset_index(drop=True)


def run_portfolio(trades: pd.DataFrame, cap: Capital, period_days: float = 1.0) -> Result:
    """Take candidate trades in time order under capital limits; build the equity curve.

    Open positions are carried at cost until they exit (conservative for a
    strategy whose positions drift up, and it avoids marking to stale quotes).
    """
    if trades.empty:
        return Result(trades, pd.DataFrame(columns=["period", "equity", "cash", "open"]), {})
    first, last = int(trades["entry_period"].min()), int(trades["exit_period"].max())
    cash = cap.bankroll
    open_pos: list[dict] = []
    taken = []
    curve = []
    by_entry = {p: g for p, g in trades.groupby("entry_period")}
    for period in range(first, last + 1):
        # 1. exits due this period
        still = []
        for pos in open_pos:
            if pos["exit_period"] <= period:
                cash += pos["shares"] * pos["proceeds"]
            else:
                still.append(pos)
        open_pos = still
        invested = sum(p["shares"] * p["cost"] for p in open_pos)
        equity = cash + invested
        # 2. entries
        todays = by_entry.get(period)
        if todays is not None:
            for tr in todays.itertuples(index=False):
                stake = cap.stake * (equity / cap.bankroll if cap.compound else 1.0)
                in_event = sum(p["shares"] * p["cost"] for p in open_pos if p["cluster"] == tr.cluster)
                room = min(stake, cap.max_event * (equity / cap.bankroll if cap.compound else 1.0) - in_event,
                           cap.max_exposure_frac * equity - invested, cash)
                themes = getattr(tr, "themes", None) or ()
                if cap.max_theme is not None:
                    for theme in themes:
                        in_theme = sum(p["shares"] * p["cost"] for p in open_pos if theme in p["themes"])
                        room = min(room, cap.max_theme - in_theme)
                if room < 0.25 * stake or room <= 0:
                    continue
                shares = room / tr.cost
                cash -= shares * tr.cost
                invested += shares * tr.cost
                open_pos.append({"shares": shares, "cost": tr.cost, "proceeds": tr.proceeds,
                                 "exit_period": tr.exit_period, "cluster": tr.cluster, "themes": themes})
                taken.append({**tr._asdict(), "shares": shares, "stake": shares * tr.cost,
                              "pnl": shares * tr.pnl_ps})
        curve.append((period, cash + invested, cash, len(open_pos)))
    # settle whatever exits after the loop's last period (none by construction)
    eq = pd.DataFrame(curve, columns=["period", "equity", "cash", "open"])
    tk = pd.DataFrame(taken)
    return Result(tk, eq, summarize(tk, eq, cap, period_days))


def summarize(tk: pd.DataFrame, eq: pd.DataFrame, cap: Capital, period_days: float = 1.0) -> dict:
    if tk.empty or eq.empty:
        return {"trades": 0}
    e = eq["equity"].to_numpy()
    rets = np.diff(e) / e[:-1]
    years = len(e) * period_days / 365.25
    peak = np.maximum.accumulate(e)
    dd = (e - peak) / peak
    per_year = 365.25 / period_days
    total = e[-1] / cap.bankroll - 1
    return {
        "trades": int(len(tk)),
        "events": int(tk["cluster"].nunique()),
        "win_rate": float((tk["pnl"] > 0).mean()),
        "avg_ret_per_trade": float(tk["ret"].mean()),
        "median_hold_days": float(tk["hold"].median() * period_days),
        "total_return": float(total),
        "cagr": float((1 + total) ** (1 / years) - 1) if years > 0 and total > -1 else float("nan"),
        "sharpe": float(rets.mean() / rets.std() * np.sqrt(per_year)) if rets.std() > 0 else float("nan"),
        "max_drawdown": float(dd.min()),
        "worst_trade": float(tk["pnl"].min()),
        "best_trade": float(tk["pnl"].max()),
        "avg_utilisation": float(1 - (eq["cash"] / eq["equity"]).mean()),
        "years": float(years),
        "final_equity": float(e[-1]),
    }

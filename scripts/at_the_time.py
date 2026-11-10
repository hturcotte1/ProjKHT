"""Universes defined by what a market had traded AT THE TIME, not by the end.

Round two chose "thin" markets by their final volume (20,000 to 100,000
shares). That number is not known when a trade is made, and it is not
neutral: a market in which the surprise happens draws a burst of trading and
ends up over the line, so the markets that *ended* thin had already shed many
of their losers (docs/05_third_round.md, section 3).

Here a market belongs to a range while the shares it has traded so far are
inside it, whatever it goes on to trade. "20,000 to 100,000 at the time" is
therefore the markets that ended there plus the early life of every market
that ended bigger. This is also what the paper accounts do: they look at the
volume a market has today.

The three sets of resolved news markets on disk:

    big       ended at 100,000 shares or more      (first round)
    thin      ended at 20,000 to 100,000           (second round)
    thinner   ended at 5,000 to 20,000             (third round)
"""

from __future__ import annotations

import gc
from pathlib import Path

import pandas as pd

from kht.data.download import load_meta
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes
from kht.research.sports import build_trades_table

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
SETS = {"big": "closed", "thin": "closed_thin", "thinner": "closed_thinner"}
CEILING = {"big": float("inf"), "thin": 100_000, "thinner": 20_000}     # every market in the set ended below this
TOP = 10**12                                                            # "no upper limit" for a range


def news_meta(name: str) -> pd.DataFrame:
    """Resolved markets outside sports and crypto.

    Earlier rounds also required "a life of two days or more", to drop daily
    markets. A market's life is not known in advance, and the markets that
    resolve within two days of opening although scheduled to run longer are
    mostly ones where the thing happened at once: losses for anyone who had
    bought "No". They are kept here. What is still dropped (a life under two
    days AND a schedule of three days or less) could not have been traded by
    any rule in this project, since all of them need more than three days to
    the scheduled end.
    """
    meta = load_meta(SETS[name])
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    scheduled = (meta["end_ts"] - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    meta = meta[(~meta["category"].isin(["sports", "crypto"])) & ((life >= 2) | (scheduled > 3)) & resolved].copy()
    meta["closed_ts"] = meta["closed_ts"].fillna(meta["end_ts"])
    return meta[meta["closed_ts"].notna()]


def all_meta() -> pd.DataFrame:
    return pd.concat([news_meta(n) for n in SETS], ignore_index=True).drop_duplicates("market_id")


def _part(name: str, ranges: list[tuple[int, int]]) -> dict[tuple[int, int], pd.DataFrame]:
    """The trades of one set of markets made while the market's volume so far was in each range (cached)."""
    paths = {r: CACHE / f"tr2_{name}_{r[0]}_{r[1]}.parquet" for r in ranges}
    todo = [r for r in ranges if not paths[r].exists()]
    if todo:
        tr = build_trades_table(news_meta(name))
        CACHE.mkdir(parents=True, exist_ok=True)
        for lo, hi in todo:
            tr[(tr["cum_before"] >= lo) & (tr["cum_before"] < hi)].reset_index(drop=True).to_parquet(paths[(lo, hi)], index=False)
        del tr
        gc.collect()
    return {r: pd.read_parquet(paths[r]) for r in ranges}


def trades(lo: int, hi: int, only: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Every trade made while its market had traded at least ``lo`` and fewer than ``hi`` shares.

    ``only`` restricts it to some of the three sets (to reproduce a universe
    chosen by final volume, e.g. ``only=("thin",)`` with 20,000-100,000).
    """
    parts = []
    for name in SETS:
        if (only is not None and name not in only) or CEILING[name] <= lo:
            continue                                  # not asked for, or no market in the set ever got that far
        parts.append(_part(name, [(lo, hi)])[(lo, hi)])
    tr = pd.concat(parts, ignore_index=True)
    return tr.sort_values(["market_id", "ts"], kind="stable").reset_index(drop=True)


def panel(lo: int, hi: int, only: tuple[str, ...] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(metadata, trades, by-side daily panel) of the markets while they had traded ``lo`` to ``hi`` shares."""
    tag = "all" if only is None else "-".join(only)
    path = CACHE / f"panel2_at_{lo}_{hi}_{tag}.parquet"
    meta = all_meta() if only is None else pd.concat([news_meta(n) for n in only], ignore_index=True).drop_duplicates("market_id")
    tr = trades(lo, hi, only)
    if path.exists():
        p = pd.read_parquet(path)
    else:
        p = add_taker_buy_pnl(by_side(period_quotes(tr, min_cum=lo), meta))
        p.to_parquet(path, index=False)
    return meta, tr, p


def account(lists: list[pd.DataFrame], bankroll: float, frac: float, exposure: float = 0.8, participation: float = 0.10):
    """One account trading several trade lists, each market bought once: at its EARLIEST entry.

    Trade lists from different universes or horizons can hold the same market
    twice (bought with four months to run, and again inside the last sixty
    days; or while thin, and again once it had grown). An account buys it the
    first time and then holds it. Keeping instead the entry from the list one
    happens to prefer would drop the early purchases of exactly those markets
    that went on to qualify again, and keep the ones that never did: the
    markets that fell out of the band or resolved against the position.
    Ties on the day go to the earlier list.

    Positions are at most ``participation`` of the dollars takers bought in
    range over the entry window and are priced at that window's average; one
    position per event, four per story. Returns (summary row, equity curve).
    """
    from kht.backtest.harvest import Capital, run_portfolio

    t = pd.concat([lst.assign(prio=i) for i, lst in enumerate(lists)], ignore_index=True)
    t = t.sort_values(["entry_period", "prio", "market_id"]).drop_duplicates("market_id", keep="first")
    t["cost"] = t["cost_vwap"]
    t["pnl_ps"] = t["proceeds"] - t["cost"]
    t["ret"] = t["pnl_ps"] / t["cost"]
    t["max_stake"] = participation * t["usd_window"]
    t = t.sort_values(["entry_period", "prio", "market_id"]).reset_index(drop=True)
    stake = bankroll * frac
    r = run_portfolio(t, Capital(bankroll=bankroll, stake=stake, max_event=stake, max_theme=4 * stake, max_exposure_frac=exposure,
                                 min_stake=min(5.0, 0.25 * stake)))
    tk, eq = r.trades, r.equity
    month = pd.to_datetime(eq["period"], unit="D").dt.to_period("M")
    monthly = eq.groupby(month)["equity"].last().pct_change().dropna()
    row = {"bankroll": bankroll, "stake": f"{100 * frac:g}%", "taken": r.stats["trades"], "average position $": float(tk["stake"].mean()),
           "cut by flow %": 100 * float((tk["stake"] < 0.98 * stake).mean()), "losers": int((tk["pnl"] < -0.5 * tk["stake"]).sum()),
           "per year %": 100 * r.stats["cagr"], "profit a year $": bankroll * r.stats["total_return"] / r.stats["years"],
           "worst drawdown %": 100 * r.stats["max_drawdown"], "money in use %": 100 * r.stats["avg_utilisation"],
           "worst month %": 100 * float(monthly.min()), "losing months %": 100 * float((monthly < 0).mean())}
    return row, eq


if __name__ == "__main__":
    # build the cached pieces: python scripts/at_the_time.py big thin [thinner]
    import sys

    for set_name in sys.argv[1:]:
        got = _part(set_name, [r for r in ((5_000, 20_000), (20_000, 100_000), (100_000, TOP)) if CEILING[set_name] > r[0]])
        for (lo_, hi_), frame in got.items():
            print(f"{set_name}: {len(frame):,} trades in {frame['market_id'].nunique():,} markets while at {lo_:,} to {hi_:,} shares")

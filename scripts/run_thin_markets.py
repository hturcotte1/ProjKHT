"""How much of the thinner markets' edge could an account actually have taken?

The second round found the first round's rule repeating, with a larger edge,
in news markets that traded only 20,000 to 100,000 shares. A market that thin
cannot take much money. This script measures how much: for each trade, the
dollars takers bought at in-range prices on the entry day and the two days
after it (the nearest thing to "how much was for sale" that history offers),
and then runs accounts whose positions are limited to a tenth of that and
priced at the average of those prints instead of the first one.

Four trade lists are combined:

    big tight   the main paper account's rule, on markets with 100,000 shares
                or more (the first round's universe)
    thin tight  the same rule on markets with 20,000 to 100,000 shares
    thin wide   90-98c instead of 95-98c, on the thinner markets
    big wide    90-98c on the big markets, where 90-95c failed its test

Exploratory. The accounts know only the losses that happened in these three
years, and they assume that taking a tenth of what others bought would not
have moved the price.

    python scripts/run_thin_markets.py
"""

from __future__ import annotations

import gc
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_quiet_favourites as rq  # noqa: E402
import run_quiet_replication as rr  # noqa: E402

from kht.backtest.harvest import Capital, Rule, candidate_trades, prepare, run_portfolio  # noqa: E402
from kht.data.download import load_meta  # noqa: E402
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes  # noqa: E402
from kht.research.sports import build_trades_table  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402
from kht.trading.universe import is_operational_tag  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
WINDOW_DAYS = 3
PARTICIPATION = 0.10


def big_meta() -> pd.DataFrame:
    meta = load_meta("closed")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    return meta[(~meta["category"].isin(["sports", "crypto"])) & (life >= 2) & resolved].copy()


def band_flow(tr: pd.DataFrame, t: pd.DataFrame, lo: float, hi: float, min_cum: float) -> pd.DataFrame:
    """Per trade: dollars and average price of taker buys of the traded outcome at in-range prices over the entry window."""
    want = t[["market_id", "side", "entry_period"]].drop_duplicates("market_id").set_index("market_id")
    x = tr[tr["market_id"].isin(want.index) & (tr["cum_before"] >= min_cum)]
    side = want["side"].reindex(x["market_id"]).to_numpy()
    entry = want["entry_period"].reindex(x["market_id"]).to_numpy()
    day = x["ts"].to_numpy() // 86_400
    dir0 = x["dir0"].to_numpy()
    p0 = x["p0"].to_numpy(dtype=np.float64)
    size = x["size"].to_numpy(dtype=np.float64)
    buys = np.where(side == 0, dir0 > 0, dir0 < 0)
    px = np.where(side == 0, p0, 1.0 - p0)
    ok = buys & (px > lo) & (px <= hi + 0.005) & (day >= entry) & (day < entry + WINDOW_DAYS)
    f = pd.DataFrame({"market_id": x["market_id"].to_numpy()[ok], "sz": size[ok], "usd": (size * px)[ok]})
    g = f.groupby("market_id")
    out = pd.DataFrame({"usd_window": g["usd"].sum(), "sz_window": g["sz"].sum()})
    out["vwap"] = out["usd_window"] / out["sz_window"]
    return out


def universe(meta: pd.DataFrame, min_cum: float, label: str) -> dict[str, pd.DataFrame]:
    """The tight and wide trade lists of one universe, each with its in-range flow and themes."""
    tr = build_trades_table(meta)
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(tr, min_cum=min_cum), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    single = ~meta.set_index("market_id")["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    ask, dte = s["ask"].to_numpy(), s["days_to_end"].to_numpy()
    ok = (dte > 3) & (dte <= 60) & single
    rng14, seasoned14 = rq.trailing_range(s, 14)
    calm = ~(seasoned14 & (rng14 > 0.15))
    tag_lists = meta.set_index("market_id")["tags"].fillna("").str.split("|")
    counts = tag_lists.explode().value_counts()
    theme_set = {x for x in counts[(counts >= 2) & (counts <= max(2, 0.10 * len(meta)))].index if x and not is_operational_tag(x)}
    themes_of = tag_lists.map(lambda tags: tuple(sorted(set(tags) & theme_set)))
    lists = {}
    for name, lo, hi, extra in (("tight", 0.95, 0.98, True), ("wide", 0.90, 0.98, True), ("wide, calm only", 0.90, 0.98, calm)):
        t = candidate_trades(s, Rule(lo, hi, 3, 60), signal=(ask > lo) & (ask <= hi) & ok & extra)
        t = t.join(band_flow(tr, t, lo, hi, min_cum), on="market_id")
        fee_rate = t["entry_fee"] / (t["entry_px"] * (1 - t["entry_px"]))
        t["cost_vwap"] = t["vwap"] + fee_rate * t["vwap"] * (1 - t["vwap"])
        t["ret_vwap"] = (t["proceeds"] - t["cost_vwap"]) / t["cost_vwap"]
        t["themes"] = t["market_id"].map(themes_of)
        t["universe"] = label
        lists[f"{label} {name}"] = t
    del tr, s
    gc.collect()
    return lists


def describe(name: str, t: pd.DataFrame) -> dict:
    a = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    b = mean_cluster(t["ret_vwap"].to_numpy(), t["cluster"].to_numpy())
    years = (t["entry_period"].max() - t["entry_period"].min()) / 365.25
    q = t["usd_window"].quantile([0.10, 0.50, 0.90])
    return {"trades": name, "n": len(t), "a year": len(t) / years, "lost": int((t["won"] == 0).sum()),
            "ret % at first print": 100 * a.mean, "t": a.t, "ret % at 3-day average": 100 * b.mean, "t ": b.t,
            "median hold, days": float(t["hold"].median()),
            "in-range $ bought: 10th pct": q[0.10], "median": q[0.50], "90th pct": q[0.90],
            "trades with under $200 in range": 100 * float((t["usd_window"] < 200).mean())}


def account(lists: list[pd.DataFrame], bankroll: float, frac: float) -> dict:
    """Trade the lists in priority order (a market is bought once), positions capped at a tenth of the in-range flow."""
    seen: set[int] = set()
    parts = []
    for i, t in enumerate(lists):
        t = t[~t["market_id"].isin(seen)].assign(prio=i)
        seen |= set(t["market_id"])
        parts.append(t)
    t = pd.concat(parts, ignore_index=True)
    t["cost"] = t["cost_vwap"]
    t["pnl_ps"] = t["proceeds"] - t["cost"]
    t["ret"] = t["pnl_ps"] / t["cost"]
    t["max_stake"] = PARTICIPATION * t["usd_window"]
    t = t.sort_values(["entry_period", "prio", "market_id"]).reset_index(drop=True)
    stake = bankroll * frac
    r = run_portfolio(t, Capital(bankroll=bankroll, stake=stake, max_event=stake, max_theme=4 * stake, max_exposure_frac=0.8,
                                 min_stake=min(5.0, 0.25 * stake)))
    tk = r.trades
    return {"bankroll": bankroll, "stake": f"{100 * frac:g}%", "taken": r.stats["trades"], "average position $": float(tk["stake"].mean()),
            "cut by flow %": 100 * float((tk["stake"] < 0.98 * stake).mean()), "losers": int((tk["pnl"] < -0.5 * tk["stake"]).sum()),
            "per year %": 100 * r.stats["cagr"], "profit a year $": bankroll * r.stats["total_return"] / r.stats["years"],
            "worst drawdown %": 100 * r.stats["max_drawdown"], "money in use %": 100 * r.stats["avg_utilisation"]}


def main() -> None:
    lists = universe(big_meta(), 100_000, "big")
    lists.update(universe(rr.thin_meta(), 20_000, "thin"))
    summary = pd.DataFrame([describe(k, v) for k, v in lists.items()])
    summary.to_csv(OUT / "t_thin_trades.csv", index=False)
    print("the trade lists (first print as in every backtest; 3-day average as a larger order would pay)\n")
    print(summary.round(2).to_string(index=False))

    combos = {
        "A. big tight (the main paper account today)": ["big tight"],
        "B. A + thin tight": ["big tight", "thin tight"],
        "C. A + thin wide": ["big tight", "thin wide"],
        "D. A + thin wide, calm only": ["big tight", "thin wide, calm only"],
        "E. big wide + thin wide, calm only": ["big wide, calm only", "thin wide, calm only"],
    }
    rows = []
    for name, keys in combos.items():
        for bankroll in (1_000, 5_000, 25_000):
            for frac in (0.02, 0.04):
                rows.append({"account": name, **account([lists[k] for k in keys], bankroll, frac)})
    acc = pd.DataFrame(rows)
    acc.to_csv(OUT / "t_thin_accounts.csv", index=False)
    print(f"\naccounts: positions at most {PARTICIPATION:.0%} of the in-range flow, priced at the 3-day average, one position per event, "
          "four per story, at most 80% invested\n")
    print(acc.round(1).to_string(index=False))


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for st in self.streams:
            st.write(text)

    def flush(self):
        for st in self.streams:
            st.flush()


if __name__ == "__main__":
    with (OUT / "thin_markets_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__

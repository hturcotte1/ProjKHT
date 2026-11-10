"""How much money could the main account's rule have absorbed?

The backtest buys $20 at the first taker-buy print after the signal. That says
nothing about a larger account, so this script asks the tape: in each market
the rule traded, how many dollars did takers actually buy at in-range prices
on the entry day and the two days after it? A position is then limited to a
fixed share of that flow (the *participation rate*) and is priced at the
volume-weighted average of those prints rather than at the first one.

This is exploratory and rests on one assumption that cannot be checked from
history: that taking, say, a tenth of what others bought at those prices would
not have moved them. Historical order books are not published, so the resting
depth is unknown; observed flow is the nearest thing to it.

Usage: python scripts/run_capacity.py [--out reports/research]
"""

from __future__ import annotations

import argparse
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.backtest.harvest import Capital, Rule, candidate_trades, prepare, run_portfolio
from kht.data.download import load_meta
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes
from kht.research.sports import build_trades_table
from kht.research.stats import mean_cluster
from kht.trading.universe import is_operational_tag

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
SPLIT_TS = pd.Timestamp("2026-05-01", tz="UTC").timestamp()
ASK_LO, ASK_HI = 0.95, 0.98
WINDOW_DAYS = 3                      # the backtest waits up to three days for an entry print
MIN_CUM = 100_000                    # same ex-ante universe as everything else
PARTICIPATION = (0.05, 0.10, 0.25)
BANKROLLS = (1_000, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000)


def band_flow(tr: pd.DataFrame, t: pd.DataFrame) -> pd.DataFrame:
    """Per trade: dollars and VWAP of taker buys of the traded outcome at
    in-range prices, on the entry day alone and over the entry window."""
    want = t[["market_id", "side", "entry_period"]].drop_duplicates("market_id").set_index("market_id")
    x = tr[tr["market_id"].isin(want.index) & (tr["cum_before"] >= MIN_CUM)]
    side = want["side"].reindex(x["market_id"]).to_numpy()
    entry = want["entry_period"].reindex(x["market_id"]).to_numpy()
    day = x["ts"].to_numpy() // 86_400
    dir0 = x["dir0"].to_numpy()
    p0 = x["p0"].to_numpy(dtype=np.float64)
    size = x["size"].to_numpy(dtype=np.float64)
    buys = np.where(side == 0, dir0 > 0, dir0 < 0)            # a taker sell of outcome 0 is a taker buy of outcome 1
    px = np.where(side == 0, p0, 1.0 - p0)
    ok = buys & (px > ASK_LO) & (px <= ASK_HI + 0.005) & (day >= entry) & (day < entry + WINDOW_DAYS)
    f = pd.DataFrame({"market_id": x["market_id"].to_numpy()[ok], "first_day": (day == entry)[ok],
                      "sz": size[ok], "usd": (size * px)[ok]})
    g = f.groupby("market_id")
    out = pd.DataFrame({"usd_window": g["usd"].sum(), "sz_window": g["sz"].sum(), "prints": g.size()})
    out["usd_day1"] = f[f["first_day"]].groupby("market_id")["usd"].sum().reindex(out.index).fillna(0.0)
    out["vwap"] = out["usd_window"] / out["sz_window"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/research")
    args = ap.parse_args()
    out = Path(args.out)
    t0 = time.time()

    meta = load_meta("closed")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    meta = meta[(~meta["category"].isin(["sports", "crypto"])) & (life >= 2) & resolved].copy()
    tr = build_trades_table(meta)
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(tr), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    info = meta.set_index("market_id")
    single = ~info["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    sig = ((s["ask"] > ASK_LO) & (s["ask"] <= ASK_HI) & (s["days_to_end"] > 3) & (s["days_to_end"] <= 60)).to_numpy() & single
    t = candidate_trades(s, Rule(ASK_LO, ASK_HI, 3, 60), signal=sig)
    t["holdout"] = t["market_id"].map(s.groupby("market_id")["end_ts"].first() < SPLIT_TS)
    print(f"{len(t):,} trades of the main account's rule; tape loaded in {time.time() - t0:.0f}s")

    flow = band_flow(tr, t)
    del tr
    t = t.join(flow, on="market_id")
    assert t["usd_window"].notna().all(), "every trade was entered at an in-range print, so each has flow"
    fee_rate = t["entry_fee"] / (t["entry_px"] * (1 - t["entry_px"]))
    t["cost_first"] = t["cost"]
    t["cost_vwap"] = t["vwap"] + fee_rate * t["vwap"] * (1 - t["vwap"])
    t["ret_vwap"] = (t["proceeds"] - t["cost_vwap"]) / t["cost_vwap"]

    # ---- 1. how much traded at in-range prices
    q = [0.10, 0.25, 0.50, 0.75, 0.90]
    dist = pd.DataFrame({
        "entry day, $": t["usd_day1"].quantile(q), f"{WINDOW_DAYS}-day window, $": t["usd_window"].quantile(q),
    }).rename_axis("quantile").reset_index()
    dist.to_csv(out / "k_capacity_flow_quantiles.csv", index=False)
    print("\ndollars takers bought at in-range prices, per traded market\n",
          dist.round({"quantile": 2, dist.columns[1]: 0, dist.columns[2]: 0}).to_string(index=False))
    years = (t["entry_period"].max() - t["entry_period"].min()) / 365.25
    print(f"mean per market: ${t['usd_window'].mean():,.0f}; all markets: ${t['usd_window'].sum() / years:,.0f} a year over {years:.1f} years")

    # ---- 2. the same trades priced at the first print and at the window's VWAP
    rows = []
    for name, mask in (("holdout", t["holdout"]), ("recent", ~t["holdout"]), ("all", np.ones(len(t), bool))):
        g = t[mask]
        a = mean_cluster(g["ret"].to_numpy(), g["cluster"].to_numpy())
        b = mean_cluster(g["ret_vwap"].to_numpy(), g["cluster"].to_numpy())
        w = g["usd_window"].to_numpy()
        rows.append({"sample": name, "trades": len(g), "first print: ret %": 100 * a.mean, "t": a.t,
                     "window VWAP: ret %": 100 * b.mean, "t ": b.t,
                     "flow-weighted VWAP ret %": 100 * float((g["ret_vwap"] * w).sum() / w.sum()),
                     "avg first print": g["entry_px"].mean(), "avg VWAP": g["vwap"].mean()})
    price = pd.DataFrame(rows)
    price.to_csv(out / "k_capacity_entry_price.csv", index=False)
    print("\nreturn per trade by entry price\n", price.round(3).to_string(index=False))

    # by size of market flow: is the edge in the thin markets only?
    t["flow_bucket"] = pd.qcut(t["usd_window"], 4, labels=["thinnest", "thin", "thick", "thickest"])
    rows = []
    for b_, g in t.groupby("flow_bucket", observed=True):
        r = mean_cluster(g["ret_vwap"].to_numpy(), g["cluster"].to_numpy())
        rows.append({"in-range flow": b_, "trades": len(g), "median flow $": g["usd_window"].median(),
                     "ret % at VWAP": 100 * r.mean, "t": r.t, "win %": 100 * float((g["proceeds"] > g["cost_vwap"]).mean())})
    byflow = pd.DataFrame(rows)
    byflow.to_csv(out / "k_capacity_by_flow.csv", index=False)
    print("\nby how much traded in range\n", byflow.round(2).to_string(index=False))

    # ---- 3. where the dollars are. Flow is extremely concentrated, so a
    # position that simply follows the flow ends up mostly in a few markets.
    order = t.sort_values("usd_window", ascending=False)
    total = float(order["usd_window"].sum())
    for frac in (0.01, 0.05, 0.10):
        k = max(1, int(round(frac * len(order))))
        print(f"the {k} markets with most in-range flow ({frac:.0%} of them) hold {order['usd_window'].head(k).sum() / total:.0%} of it")
    big = order.head(10).assign(question=lambda d: info["question"].reindex(d["market_id"]).to_numpy())
    big = big[["question", "category", "holdout", "usd_window", "vwap", "proceeds"]].rename(
        columns={"usd_window": "in-range flow $", "proceeds": "paid"})
    big.to_csv(out / "k_capacity_largest_markets.csv", index=False)
    print("\nthe ten markets with most in-range flow\n", big.round(3).to_string(index=False))
    lost = t["proceeds"] < t["cost_vwap"]
    print(f"\n{int(lost.sum())} of {len(t)} trades lost; their in-range flow: median ${t.loc[lost, 'usd_window'].median():,.0f} "
          f"against ${t['usd_window'].median():,.0f} for all trades")
    rows = []
    rate = 0.10
    for cap_usd in (500, 2_000, 5_000, 10_000, 25_000, 100_000, np.inf):
        w = np.minimum(rate * t["usd_window"], cap_usd)
        rows.append({"largest position $": cap_usd, "bought per year $": float(w.sum() / years),
                     "dollar-weighted ret %": 100 * float((t["ret_vwap"] * w).sum() / w.sum()),
                     "profit per year $": float((t["ret_vwap"] * w).sum() / years),
                     "lost in losers per year $": float(-(t["ret_vwap"] * w)[lost].sum() / years)})
    ceiling = pd.DataFrame(rows)
    ceiling.to_csv(out / "k_capacity_ceiling.csv", index=False)
    print(f"\nevery trade taken at {rate:.0%} of its in-range flow, with a ceiling on the position (no account limits)\n",
          ceiling.round(2).to_string(index=False))

    # ---- 4. accounts of different sizes, positions limited to a share of the flow
    tag_lists = meta.set_index("market_id")["tags"].fillna("").str.split("|")
    counts = tag_lists.explode().value_counts()
    limit = max(2, 0.10 * len(meta))
    theme_set = {x for x in counts[(counts >= 2) & (counts <= limit)].index if x and not is_operational_tag(x)}
    t["themes"] = t["market_id"].map(tag_lists.map(lambda tags: tuple(sorted(set(tags) & theme_set))))
    tv = t.copy()
    tv["cost"] = tv["cost_vwap"]
    tv["pnl_ps"] = tv["proceeds"] - tv["cost"]
    tv["ret"] = tv["pnl_ps"] / tv["cost"]
    rows = []
    for rate in PARTICIPATION:
        tv["max_stake"] = rate * tv["usd_window"]
        for bank in BANKROLLS:
            stake = 0.02 * bank                               # the paper account's proportions
            r = run_portfolio(tv, Capital(bankroll=bank, stake=stake, max_event=stake, max_theme=0.08 * bank,
                                          max_exposure_frac=0.8, min_stake=5.0))
            st, tk = r.stats, r.trades
            rows.append({"participation": rate, "bankroll": bank, "target stake": stake, "trades": st["trades"],
                         "avg stake": float(tk["stake"].mean()), "limited by flow %": 100 * float((tk["stake"] < 0.999 * stake).mean()),
                         "money in use %": 100 * st["avg_utilisation"], "per year %": 100 * st["cagr"],
                         "profit per year $": (st["final_equity"] - bank) / st["years"],
                         "max drawdown %": 100 * st["max_drawdown"], "years": st["years"]})
    acct = pd.DataFrame(rows)
    acct.to_csv(out / "k_capacity_accounts.csv", index=False)
    for rate in PARTICIPATION:
        print(f"\naccounts when a position may be at most {rate:.0%} of the in-range flow (2% of bankroll per position, "
              "one per event, 8% per theme, 80% maximum exposure)\n",
              acct[acct["participation"] == rate].drop(columns="participation").round(1).to_string(index=False))
    t.drop(columns=["themes", "flow_bucket"]).to_csv(out / "k_capacity_trades.csv", index=False)
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

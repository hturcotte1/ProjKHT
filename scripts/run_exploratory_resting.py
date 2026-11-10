"""Exploratory: the round-trip trades of part A3, entered with a resting bid.

Part A3 of ``run_exploratory.py`` bought at the ask after a one-day move and
sold at the bid a few days later, and lost about the cost of a round trip in
every cell. The one cell family that came close to break-even was large falls
in fee-free markets. This script asks the obvious follow-up with the *same*
grid and no new choices: what if the entry is a bid resting at the signal
day's closing bid, filled only when a later taker sell prints strictly through
it (the same fill rule as the pre-registered R1m), and the exit is unchanged
(sell at the bid after the holding period, paying the fee)?

A resting bid saves the spread on the way in but is filled only when the
price keeps falling, so this is as much a test of adverse selection as of
reversal. Nothing here was fixed before the data had been seen in other
forms; treat any positive cell as a lead to forward-test, not a finding.

Usage: python scripts/run_exploratory_resting.py [--out reports/research]
"""

from __future__ import annotations

import argparse
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.backtest.harvest import Rule, candidate_trades, prepare
from kht.data.download import load_meta
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes
from kht.research.sports import build_trades_table
from kht.research.stats import mean_cluster

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
SPLIT_TS = pd.Timestamp("2026-05-01", tz="UTC").timestamp()
BAND = dict(ask_lo=0.10, ask_hi=0.90)


def rstats(t: pd.DataFrame, label: str) -> dict:
    if len(t) < 30:
        return {"rule": label, "trades": len(t)}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy(), t["entry_period"].to_numpy())   # event x day, as in A3
    return {"rule": label, "trades": len(t), "events": int(t["cluster"].nunique()),
            "win%": 100 * float((t["pnl_ps"] > 0).mean()), "avg_entry": float(t["entry_px"].mean()),
            "avg_pnl_c": 100 * float(t["pnl_ps"].mean()), "avg_ret%": 100 * r.mean, "t": r.t,
            "med_hold_d": float(t["hold"].median())}


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
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(build_trades_table(meta)), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    mid = np.where(s["ask"].notna() & s["bid"].notna() & ((s["ask"] - s["bid"]).between(-0.005, 0.10)),
                   0.5 * (s["ask"] + s["bid"]), s["last"])
    s["mid"] = mid
    g = s.groupby("series", sort=False)
    chg = (s["mid"] - g["mid"].shift(1)).where((s["period"] - g["period"].shift(1)) <= 2)
    geo = (s["category"] == "geopolitics").to_numpy()
    holdout = (s["end_ts"] < SPLIT_TS).to_numpy()
    quiet = (chg.abs() < 0.01).to_numpy() & (s["period"].to_numpy() % 7 == 0)
    print(f"panel ready in {time.time() - t0:.0f}s: {len(s):,} side-days")

    rows = []
    for universe, base in (("all categories", np.ones(len(s), bool)), ("fee-free only", geo)):
        for thr in (0.10, 0.20):
            for hold in (1, 3):
                for label, sig in (("fell", (chg <= -thr).to_numpy()), ("rose", (chg >= thr).to_numpy())):
                    name = f"{universe}: what {label} >= {int(100 * thr)}c, hold {hold}d"
                    for entry in ("taker", "maker"):
                        t = candidate_trades(s, Rule(**BAND, hold_periods=hold, reentry=True, entry=entry), signal=sig & base)
                        rows.append({"entry": entry, "sample": "all", **rstats(t, name)})
                        if entry == "maker" and len(t):
                            h = t["market_id"].map(pd.Series(holdout, index=s["market_id"]).groupby(level=0).first())
                            rows.append({"entry": entry, "sample": "scheduled end before May 2026", **rstats(t[h.to_numpy()], name)})
                            rows.append({"entry": entry, "sample": "scheduled end from May 2026", **rstats(t[~h.to_numpy()], name)})
        for entry in ("taker", "maker"):
            t = candidate_trades(s, Rule(**BAND, hold_periods=3, reentry=True, entry=entry), signal=quiet & base)
            rows.append({"entry": entry, "sample": "all", **rstats(t, f"{universe}: benchmark, no move, hold 3d")})
    res = pd.DataFrame(rows)
    res.to_csv(out / "x_a3c_roundtrip_resting_bid.csv", index=False)
    full = res[res["sample"] == "all"]
    wide = full.pivot(index="rule", columns="entry", values=["trades", "avg_ret%", "t"]).reindex(full["rule"].unique())
    print("\nround trips, whole sample: bought at the ask versus with a resting bid\n", wide.round(2).to_string())
    print("\nresting-bid cells by half of the sample\n",
          res[(res["entry"] == "maker") & (res["sample"] != "all")][["rule", "sample", "trades", "avg_ret%", "t"]].round(2).to_string(index=False))
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

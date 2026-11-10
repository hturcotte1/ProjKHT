"""Confirmatory test of the sports rule S1 (docs/01_thinking_session.md, section 8).

S1 was fixed after seeing only games that started on or after 2026-09-22.
HOLDOUT = games that started before that date.

Usage: python scripts/run_confirmatory_sports.py [--out reports/research] [--dry-run]
"""

from __future__ import annotations

import argparse
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.data.download import load_meta
from kht.research.sports import build_pregame_trades
from kht.research.stats import calibration_slope, mean_cluster
from kht.research.tapes import league_of

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)

SPLIT_TS = pd.Timestamp("2026-09-22", tz="UTC").timestamp()
SIGNAL_LEAD_H = 6.0
LOOKBACK_H = 12.0
MIN_CUM = 100_000
FEE_RATE = 0.05
RELIABLE_START = {"nfl", "nba", "mlb", "nhl", "cfb", "ncaa-basketball", "wnba", "soccer", "ufc"}


def build_trades(tr: pd.DataFrame, meta: pd.DataFrame, lo: float, hi: float) -> pd.DataFrame:
    """Signal six hours before the start; entry at the next taker-buy print before the start."""
    lead_h = tr["lead_s"].to_numpy() / 3600.0
    early = tr[lead_h > SIGNAL_LEAD_H]
    cum = early.groupby("market_id")["size"].sum().rename("cum_before_signal")
    win = tr[(lead_h > SIGNAL_LEAD_H) & (lead_h <= SIGNAL_LEAD_H + LOOKBACK_H)]
    late = tr[(lead_h <= SIGNAL_LEAD_H) & (lead_h > 0)]
    rows = []
    for side in (0, 1):
        want = 1 if side == 0 else -1                       # taker buys of this side
        sig = win[win["dir0"] == want].groupby("market_id")["p0"].last()
        ent = late[late["dir0"] == want].groupby("market_id")["p0"].first()
        ent_lead = late[late["dir0"] == want].groupby("market_id")["lead_s"].first() / 3600.0
        d = pd.concat([sig.rename("sig"), ent.rename("ent"), ent_lead.rename("entry_lead_h")], axis=1)
        if side == 1:
            d["sig"], d["ent"] = 1 - d["sig"], 1 - d["ent"]
        d["side"] = side
        rows.append(d.reset_index())
    d = pd.concat(rows, ignore_index=True).merge(cum.reset_index(), on="market_id", how="left")
    m = meta.set_index("market_id")
    d["winner"] = m["winner"].reindex(d["market_id"]).to_numpy()
    d["won"] = np.where(d["winner"] == d["side"], 1.0, np.where(d["winner"].notna(), 0.0, np.nan))
    ev = m["event_id"].reindex(d["market_id"]).to_numpy()
    d["cluster"] = np.where(ev >= 0, ev, -d["market_id"].to_numpy())
    d["game_start_ts"] = m["game_start_ts"].reindex(d["market_id"]).to_numpy()
    d["day"] = (d["game_start_ts"] // 86_400).astype(int)
    d["league"] = m["tags"].reindex(d["market_id"]).map(league_of).to_numpy()
    d["holdout"] = d["game_start_ts"] < SPLIT_TS
    ok = (d["cum_before_signal"] >= MIN_CUM) & (d["sig"] > lo) & (d["sig"] <= hi) & d["won"].notna()
    ok &= d["ent"].notna() & (d["ent"] > lo) & (d["ent"] <= hi + 0.005)
    t = d[ok].copy()
    t["fee"] = FEE_RATE * t["ent"] * (1 - t["ent"])
    t["cost"] = t["ent"] + t["fee"]
    t["ret"] = (t["won"] - t["cost"]) / t["cost"]
    t["gross_c"] = 100 * (t["won"] - t["ent"])
    return t


def stats(t: pd.DataFrame) -> dict:
    if len(t) < 10:
        return {"trades": len(t)}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy(), t["day"].to_numpy())
    r1 = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    return {"trades": len(t), "events": int(t["cluster"].nunique()), "win%": 100 * t["won"].mean(),
            "avg_entry": t["ent"].mean(), "gross_c": t["gross_c"].mean(), "avg_ret%": 100 * r.mean,
            "t_2way": r.t, "t_event": r1.t}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/research")
    ap.add_argument("--dry-run", action="store_true", help="code check on the already-examined slice only")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    meta = load_meta("closed")
    ml = meta[(meta["category"] == "sports") & (meta["sports_type"] == "moneyline") & meta["game_start_ts"].notna()]
    if args.dry_run:
        ml = ml[ml["game_start_ts"] >= SPLIT_TS]
        print("DRY RUN: already-examined games only")
    tr = build_pregame_trades(ml)
    print(f"{len(tr):,} pre-game trades in {tr['market_id'].nunique():,} games ({time.time() - t0:.0f}s)")

    rules = {"S1 favourites 75-95c": (0.75, 0.95), "control: underdogs 5-25c": (0.05, 0.25),
             "favourites 60-75c": (0.60, 0.75), "favourites 90-97c": (0.90, 0.97), "near coin flips 45-55c": (0.45, 0.55)}
    rows, keep = [], {}
    for label, (lo, hi) in rules.items():
        t = build_trades(tr, ml, lo, hi)
        keep[label] = t
        for name, mask in (("holdout", t["holdout"]), ("discovery", ~t["holdout"])):
            rows.append({"rule": label, "sample": name, **stats(t[mask])})
    res = pd.DataFrame(rows)
    res.to_csv(out / "s1_rules.csv", index=False)
    for name in ("holdout", "discovery"):
        print(f"\n[{name}]\n", res[res["sample"] == name].drop(columns="sample").round(2).to_string(index=False))

    s1 = keep["S1 favourites 75-95c"]
    s1.to_csv(out / "s1_trades.csv", index=False)
    h = s1[s1["holdout"]].copy()
    if len(h) > 50:
        h["quarter"] = pd.to_datetime(h["game_start_ts"], unit="s").dt.to_period("Q").astype(str)
        h["reliable_start"] = h["league"].isin(RELIABLE_START)
        h["px_bin"] = pd.cut(h["ent"], [0.75, 0.80, 0.85, 0.90, 0.955])
        rob = []
        for dim in ("league", "quarter", "reliable_start", "px_bin"):
            for level, g in h.groupby(dim, observed=True):
                rob.append({"dimension": dim, "level": str(level), **stats(g)})
        rob = pd.DataFrame(rob)
        rob.to_csv(out / "s1_holdout_breakdowns.csv", index=False)
        print("\nS1 holdout breakdowns\n", rob.round(2).to_string(index=False))

    # calibration of the pre-game price (six hours out), both samples
    cal = []
    base = build_trades(tr, ml, 0.03, 0.97)
    for name, g in (("holdout", base[base["holdout"]]), ("discovery", base[~base["holdout"]])):
        g0 = g[g["side"] == 0]
        if len(g0) > 300:
            a, b, se_a, se_b = calibration_slope(g0["ent"].to_numpy(), g0["won"].to_numpy(), g0["cluster"].to_numpy())
            cal.append({"sample": name, "slope": b, "se": se_b, "t_vs_1": (b - 1) / se_b, "n": len(g0)})
    cal = pd.DataFrame(cal)
    cal.to_csv(out / "s1_calibration.csv", index=False)
    print("\ncalibration slope of the entry price (slope > 1: favourites underpriced)\n", cal.round(3).to_string(index=False))
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

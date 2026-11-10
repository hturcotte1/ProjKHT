"""Run the first-pass hypothesis tests H1-H8 on the quoted-price panel.

NOTE: this panel selects markets by their *total* volume, which turned out to
bias several of these tests (see docs/02_research_findings.md, "The sample
that lied"). It is kept because that comparison is itself a finding; the tests
that count are scripts/run_confirmatory*.py and scripts/run_exploratory.py,
which use the no-hindsight sample built from trade tapes.

Usage:
    python scripts/run_research.py [--out reports/research] [--only H1,H3]

Reads data/meta/closed.parquet and data/prices/3h/*.parquet (see
scripts/download_research_data.py).
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from kht.data.download import load_meta, load_price_panel
from kht.research import hypotheses as H
from kht.research.dataset import make_dataset, tradable

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 400)


def cents(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Show price changes in cents per share."""
    out = df.copy()
    for c in cols:
        if c in out:
            out[c] = out[c] * 100
    return out


def section(title: str) -> None:
    print("\n" + "=" * 100 + f"\n{title}\n" + "=" * 100, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/research")
    ap.add_argument("--only", default="")
    ap.add_argument("--sample-frac", type=float, default=1.0,
                    help="use a random fraction of markets (the full panel needs ~10 GB of memory)")
    args = ap.parse_args()
    only = {x.strip().upper() for x in args.only.split(",") if x.strip()}
    want = lambda h: not only or h in only  # noqa: E731
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    meta = load_meta("closed")
    prices = load_price_panel("3h")
    if args.sample_frac < 1.0:
        ids = pd.Series(prices["market_id"].unique()).sample(frac=args.sample_frac, random_state=0)
        prices = prices[prices["market_id"].isin(ids)]
    print(f"loaded {prices['market_id'].nunique()} markets, {len(prices):,} price points ({time.time() - t0:.0f}s)")
    d12, _ = make_dataset(prices, meta, "12h")
    d3, _ = make_dataset(prices, meta, "3h")
    for name, d in (("12h", d12), ("3h", d3)):
        tr = d[tradable(d)]
        print(f"{name} panel: {len(d):,} rows, {d['market_id'].nunique():,} markets, "
              f"{tr['cluster'].nunique():,} events; tradable rows {len(tr):,}; "
              f"{pd.to_datetime(d['ts'].min(), unit='s').date()} .. {pd.to_datetime(d['ts'].max(), unit='s').date()}")
    summary = {
        "markets_12h": int(d12["market_id"].nunique()), "rows_12h": int(len(d12)),
        "markets_3h": int(d3["market_id"].nunique()), "rows_3h": int(len(d3)),
    }
    pd.Series(summary).to_csv(out / "sample.csv", header=["value"])

    if want("H1"):
        section("H1 momentum: slope of next change on past change (skip one bar)")
        for name, d in (("12h", d12), ("3h", d3)):
            r = H.h1_momentum(d)
            r.to_csv(out / f"h1_momentum_{name}.csv", index=False)
            piv_b = r[r.group == "all"].pivot(index="past", columns="next", values="beta")
            piv_t = r[r.group == "all"].pivot(index="past", columns="next", values="t")
            order = list(d.attrs["horizons"])
            print(f"\n[{name}] all markets: beta\n", piv_b.loc[order, order].round(4))
            print(f"[{name}] all markets: t\n", piv_t.loc[order, order].round(2))
            key = "1d"
            sub = r[(r.past == key) & (r.next == key)][["group", "beta", "se", "t", "n", "clusters"]]
            print(f"[{name}] past {key} -> next {key} by category\n", sub.round(4).to_string(index=False))
            # out-of-sample check: same regression in each calendar half
            half = d["ts"] <= d["ts"].median()
            for label, part in (("first half", d[half]), ("second half", d[~half])):
                part.attrs = d.attrs
                rh = H.h1_momentum(part, by_category=False)
                pb = rh.pivot(index="past", columns="next", values="t")
                print(f"[{name}] {label}: t\n", pb.loc[order, order].round(2))
                rh.to_csv(out / f"h1_momentum_{name}_{label.replace(' ', '_')}.csv", index=False)

    if want("H2"):
        section("H2 response to jumps: continuation (cents) in the direction of the past move")
        for name, d, past, nexts in (("12h", d12, "12h", ["12h", "1d", "3d", "7d"]), ("12h", d12, "1d", ["1d", "3d", "7d"]),
                                     ("3h", d3, "3h", ["3h", "12h", "1d", "3d"]), ("3h", d3, "1d", ["1d", "3d"])):
            r = H.h2_jump_response(d, past, nexts)
            r.to_csv(out / f"h2_jump_{name}_past{past}.csv", index=False)
            rc = cents(r, ["cont", "se"])
            print(f"\n[{name}] past move over {past}: continuation in cents\n",
                  rc.pivot(index="abs_move", columns="next", values="cont").reindex([str(c) for c in pd.IntervalIndex.from_breaks(H.JUMP_BINS)]).round(3))
            print("t-stats\n", r.pivot(index="abs_move", columns="next", values="t").reindex([str(c) for c in pd.IntervalIndex.from_breaks(H.JUMP_BINS)]).round(2))
            rcat = H.h2_jump_response(d, past, nexts[:2], group_col="category")
            rcat.to_csv(out / f"h2_jump_{name}_past{past}_by_category.csv", index=False)

    if want("H3"):
        section("H3 compression / favourite-longshot: calibration slope (>1 = compressed toward 50%)")
        snap = H.snapshots(d12[~d12["is_recurring"].fillna(False)], [0.5, 1, 3, 7, 14, 30, 60])
        cal = H.h3_calibration(snap)
        cal.to_csv(out / "h3_calibration.csv", index=False)
        print(cal.pivot(index="group", columns="lead_days", values="slope").round(3))
        print("t-stat versus slope = 1\n", cal.pivot(index="group", columns="lead_days", values="t_vs_1").round(2))
        print("n\n", cal.pivot(index="group", columns="lead_days", values="n"))
        bins = H.h3_price_bins(snap)
        bins.to_csv(out / "h3_price_bins.csv", index=False)
        bc = cents(bins, ["mean", "se"])
        print("\nmean change to resolution (cents) by quoted price, both sides of each market\n",
              bc.pivot(index="price_bin", columns="lead_days", values="mean").reindex([str(c) for c in pd.IntervalIndex.from_breaks(H.PRICE_BINS)]).round(2))
        print("t\n", bins.pivot(index="price_bin", columns="lead_days", values="t").reindex([str(c) for c in pd.IntervalIndex.from_breaks(H.PRICE_BINS)]).round(2))

    if want("H4"):
        section("H4 'something happens' bias: drift of the Yes token (cents)")
        r = H.h4_yes_drift(d12, ["1d", "7d"])
        r.to_csv(out / "h4_yes_drift.csv", index=False)
        print(cents(r, ["mean", "se"]).round(3).to_string(index=False))

    if want("H5"):
        section("H5 pre-game drift in sports (favourite side, cents)")
        for name, d, leads, ref, early in (("12h", d12, [12, 24, 48, 72, 120], 24, 72), ("3h", d3, [3, 6, 12, 24, 48, 72], 24, 72),
                                           ("3h", d3, [3, 6, 12, 24, 48, 72], 6, 24)):
            tab = H.pregame_table(d, leads)
            tab.to_parquet(out / f"h5_pregame_table_{name}.parquet", index=False)
            ml = tab[tab["sports_type"] == "moneyline"]
            for label, t in (("all game markets", tab), ("moneylines", ml)):
                res = H.h5_pregame(t, ref, early)
                print(f"\n[{name}] {label}: n={len(t)}  ref=T-{ref}h early=T-{early}h")
                print(cents(res["favourite_drift"], ["mean_move", "se"]).round(3).to_string(index=False))
                print(res["momentum_and_confirmation"].round(4).to_string(index=False))
                print(res["calibration"].round(4).to_string(index=False))
                for k, v in res.items():
                    v.to_csv(out / f"h5_{k}_{name}_ref{ref}_{label.split()[0]}.csv", index=False)

    if want("H6"):
        section("H6 calendar effects: change of the favoured side over the next bar (cents)")
        for name, d, hz in (("12h", d12, "12h"), ("3h", d3, "3h")):
            r = H.h6_calendar(d, hz)
            r.to_csv(out / f"h6_calendar_{name}.csv", index=False)
            print(f"\n[{name}]\n", cents(r, ["mean_h1", "mean_h2"]).round(3).to_string(index=False))

    if want("H7"):
        section("H7 deadline markets ('by' / 'before'): drift of Yes (cents)")
        r = H.h7_deadline(d12, ["1d", "7d"])
        r.to_csv(out / "h7_deadline.csv", index=False)
        print(cents(r, ["mean", "se"]).round(3).to_string(index=False))

    if want("H8"):
        section("H8 new markets: favoured-side drift by market age (cents)")
        r = H.h8_new_market(d12, "1d")
        r.to_csv(out / "h8_new_market.csv", index=False)
        print(cents(r, ["fav_change_1d", "fav_to_res"]).round(3).to_string(index=False))

    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

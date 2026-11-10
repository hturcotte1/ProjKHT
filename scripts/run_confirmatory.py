"""Confirmatory test of rule R1 (docs/01_thinking_session.md, section 8).

R1 was fixed after seeing only markets that closed on or after 2026-06-08.
This script evaluates it, its pre-registered variants and its controls
separately on

* DISCOVERY: markets whose scheduled end is on or after 2026-05-01 (the part
  that informed the rule; also the part affected by not-yet-resolved markets);
* HOLDOUT:   markets whose scheduled end is before 2026-05-01 (not examined
  when the rule was written).

The split uses the *scheduled* end date because it is known in advance;
splitting on the realised close date would condition on the outcome.

Usage: python scripts/run_confirmatory.py [--out reports/research]
"""

from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.backtest.harvest import Capital, Rule, candidate_trades, prepare, run_portfolio
from kht.data.download import load_meta
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes
from kht.research.sports import build_trades_table
from kht.research.stats import calibration_slope, mean_cluster

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 300)

SPLIT_TS = pd.Timestamp("2026-05-01", tz="UTC").timestamp()
PRICE_BINS = [0, 0.03, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.97, 0.99, 1.0]

RULES = {
    "R1  90-97c, 3-60d, hold": Rule(0.90, 0.97, 3, 60, name="R1"),
    "R1a 90-97c, 7-60d, hold": Rule(0.90, 0.97, 7, 60, name="R1a"),
    "R1b 90-97c, 7-60d, sell 3d before end": Rule(0.90, 0.97, 7, 60, exit_dte=3, name="R1b"),
    "R1c 80-97c, 3-60d, hold": Rule(0.80, 0.97, 3, 60, name="R1c"),
    "R1d 95-99c, 3-60d, hold": Rule(0.95, 0.99, 3, 60, name="R1d"),
    "control: longshots 3-10c": Rule(0.03, 0.10, 3, 60, name="longshot"),
    "control: coin flips 40-60c": Rule(0.40, 0.60, 3, 60, name="mid"),
}


def non_sports(meta: pd.DataFrame) -> pd.DataFrame:
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    return meta[(~meta["category"].isin(["sports", "crypto"])) & (life >= 2) & resolved].copy()


def section(title: str) -> None:
    print("\n" + "=" * 110 + f"\n{title}\n" + "=" * 110, flush=True)


def trade_stats(t: pd.DataFrame) -> dict:
    """Per-trade statistics with event-clustered inference (equal dollars per trade)."""
    if len(t) < 5:
        return {"trades": len(t)}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy(), t["entry_period"].to_numpy())
    r1 = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    by_event = t.groupby("cluster")["ret"].mean()
    return {
        "trades": len(t), "events": int(t["cluster"].nunique()), "win%": 100 * float((t["proceeds"] > t["cost"]).mean()),
        "avg_entry": float(t["entry_px"].mean()), "avg_ret%": 100 * r.mean, "t_2way": r.t, "t_event": r1.t,
        "event_avg_ret%": 100 * float(by_event.mean()),
        "med_hold_d": float(t["hold"].median()), "worst%": 100 * float(t["ret"].min()),
        "ret_per_30d%": 100 * float(t["ret"].sum() / max(t["hold"].clip(lower=1).sum(), 1) * 30),
    }


def calib_table(s: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    key = pd.cut(s["ask"], PRICE_BINS)
    for level, g in s.groupby(key, observed=True):
        if len(g) < 100:
            continue
        r = mean_cluster(g["net_ps"].to_numpy(), g["cluster"].to_numpy(), g["day"].to_numpy())
        rows.append({"sample": label, "ask": str(level), "n": len(g), "events": int(g["cluster"].nunique()),
                     "avg_ask": g["ask"].mean(), "win%": 100 * g["won"].mean(),
                     "gross_c": 100 * g["gross_ps"].mean(), "net_c": 100 * r.mean, "t": r.t,
                     "net_ret%": 100 * g["net_ret"].mean(), "med_days_to_close": g["days_to_close"].median()})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/research")
    ap.add_argument("--dry-run", action="store_true",
                    help="code check only: use just the already-examined slice with an arbitrary split")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    meta = non_sports(load_meta("closed"))
    split_ts = SPLIT_TS
    if args.dry_run:
        meta = meta[meta["closed_ts"] >= pd.Timestamp("2026-06-08", tz="UTC").timestamp()]
        split_ts = pd.Timestamp("2026-09-01", tz="UTC").timestamp()
        print("DRY RUN: already-examined slice only; the 'holdout' label below is arbitrary")
    tr = build_trades_table(meta)
    have = tr["market_id"].nunique()
    print(f"{len(tr):,} trades in {have:,} markets ({time.time() - t0:.0f}s); "
          f"{pd.to_datetime(tr['ts'].min(), unit='s').date()} .. {pd.to_datetime(tr['ts'].max(), unit='s').date()}")
    q = period_quotes(tr)
    del tr
    s = prepare(add_taker_buy_pnl(by_side(q, meta)))
    s["holdout"] = s["end_ts"] < split_ts
    s = s[s["won"].notna()]
    print(f"{len(q):,} market-days after the 100k-share rule, {s['market_id'].nunique():,} markets, "
          f"{s['cluster'].nunique():,} events; holdout share of rows {s['holdout'].mean():.2f}")
    samples = {"holdout": s[s["holdout"]], "discovery": s[~s["holdout"]]}
    json.dump({"markets_with_tapes": int(have), "market_days": int(len(q)), "markets_in_panel": int(s["market_id"].nunique()),
               "events": int(s["cluster"].nunique()), "split": "scheduled end before/after 2026-05-01",
               "holdout_markets": int(samples["holdout"]["market_id"].nunique()),
               "discovery_markets": int(samples["discovery"]["market_id"].nunique())},
              open(out / "confirmatory_sample.json", "w"), indent=1)

    # ------------------------------------------------------------------ 1
    section("1. Calibration at prices a taker paid (one row per market-day-side; net of today's fees)")
    cal = pd.concat([calib_table(g[(g["ask"].notna()) & (g["days_to_close"] > 0)], name) for name, g in samples.items()])
    cal.to_csv(out / "c1_calibration_by_price.csv", index=False)
    for name in samples:
        print(f"\n[{name}]\n", cal[cal["sample"] == name].drop(columns="sample").round(2).to_string(index=False))
    rows = []
    for name, g in samples.items():
        gg = g[g["ask"].between(0.02, 0.98) & (g["side"] == 0)]
        for lab, sub in [("all", gg)] + [(c, x) for c, x in gg.groupby("category")]:
            if len(sub) < 500:
                continue
            a, b, se_a, se_b = calibration_slope(sub["ask"].to_numpy(), sub["won"].to_numpy(), sub["cluster"].to_numpy())
            rows.append({"sample": name, "group": lab, "slope": b, "se": se_b, "t_vs_1": (b - 1) / se_b,
                         "intercept": a, "n": len(sub), "events": int(sub["cluster"].nunique())})
    slopes = pd.DataFrame(rows)
    slopes.to_csv(out / "c1_calibration_slopes.csv", index=False)
    print("\ncalibration slope of outcome 0 (slope > 1: prices compressed toward 50%)\n", slopes.round(3).to_string(index=False))

    # ------------------------------------------------------------------ 2
    section("2. R1, variants and controls: every qualifying trade, equal dollars per trade")
    rows, trade_lists = [], {}
    info = meta.set_index("market_id")
    yes_no = (info["outcome0"].reindex(s["market_id"]) == "Yes").to_numpy()
    single = ~info["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    deadline = info["question"].reindex(s["market_id"]).str.contains(r"\b(?:by|before)\b", case=False, regex=True, na=False).to_numpy()
    r1_band = ((s["ask"] > 0.90) & (s["ask"] <= 0.97) & (s["days_to_end"] > 3) & (s["days_to_end"] <= 60)).to_numpy()
    buy_no = yes_no & (s["side"] == 1).to_numpy()
    extra = {
        "R2  R1, 'No' side of single yes/no markets": (Rule(0.90, 0.97, 3, 60, name="R2"), r1_band & buy_no & single),
        "R3  R2, 'by/before' questions": (Rule(0.90, 0.97, 3, 60, name="R3"), r1_band & buy_no & single & deadline),
        "R1m R1 with a resting bid (3 days)": (Rule(0.90, 0.97, 3, 60, entry="maker", name="R1m"), None),
    }
    todo = [(label, rule, None) for label, rule in RULES.items()] + [(l, r, sig) for l, (r, sig) in extra.items()]
    for label, rule, sig in todo:
        cands = candidate_trades(s, rule, signal=sig)
        if cands.empty:
            continue
        cands["holdout"] = cands["market_id"].map(s.groupby("market_id")["holdout"].first())
        trade_lists[rule.name] = cands
        cands.to_csv(out / f"c2_trades_{rule.name}.csv", index=False)
        for name, mask in (("holdout", cands["holdout"]), ("discovery", ~cands["holdout"])):
            rows.append({"rule": label, "sample": name, **trade_stats(cands[mask])})
    res = pd.DataFrame(rows)
    res.to_csv(out / "c2_rules.csv", index=False)
    for name in ("holdout", "discovery"):
        print(f"\n[{name}]\n", res[res["sample"] == name].drop(columns="sample").round(2).to_string(index=False))

    # ------------------------------------------------------------------ 3
    section("3. Robustness of R1 on the holdout")
    r1 = trade_lists["R1"]
    h = r1[r1["holdout"]].copy()
    h["year"] = pd.to_datetime(h["entry_period"] * 86_400, unit="s").dt.year
    h["half"] = pd.to_datetime(h["entry_period"] * 86_400, unit="s").dt.to_period("Q").astype(str)
    h["dte_bin"] = pd.cut(h["dte_at_signal"], [3, 7, 14, 30, 60])
    h["px_bin"] = pd.cut(h["entry_px"], [0.90, 0.93, 0.95, 0.975])
    h["outcome_side"] = np.where(h["side"] == 0, "first-listed (Yes)", "second-listed (No)")
    rob = []
    for dim in ("year", "half", "category", "dte_bin", "px_bin", "outcome_side"):
        for level, g in h.groupby(dim, observed=True):
            rob.append({"dimension": dim, "level": str(level), **trade_stats(g)})
    rob = pd.DataFrame(rob)
    rob.to_csv(out / "c3_r1_holdout_breakdowns.csv", index=False)
    print(rob.round(2).to_string(index=False))

    # concentration: results without the events that supplied the most trades,
    # and with at most one trade per event
    counts = h.groupby("cluster").size().sort_values(ascending=False)
    drop_rows = []
    for k in (0, 5, 20, 50):
        keep = h[~h["cluster"].isin(counts.index[:k])]
        drop_rows.append({"variant": f"without the {k} largest events", **trade_stats(keep)})
    one = h.sort_values("entry_period").groupby("cluster").head(1)
    drop_rows.append({"variant": "first trade of each event only", **trade_stats(one)})
    print("\nR1 holdout: concentration checks\n", pd.DataFrame(drop_rows).round(2).to_string(index=False))
    pd.DataFrame(drop_rows).to_csv(out / "c3_r1_concentration.csv", index=False)

    # event bootstrap of the mean return
    rng = np.random.default_rng(7)
    by_ev = h.groupby("cluster")["ret"].agg(["sum", "size"])
    sums, sizes = by_ev["sum"].to_numpy(), by_ev["size"].to_numpy()
    idx = rng.integers(0, len(sums), size=(5000, len(sums)))
    boot = sums[idx].sum(axis=1) / sizes[idx].sum(axis=1)
    ci = np.percentile(boot, [0.5, 2.5, 50, 97.5, 99.5])
    print(f"\nevent bootstrap of R1 holdout mean return per trade: median {100 * ci[2]:.2f}%, "
          f"95% CI [{100 * ci[1]:.2f}%, {100 * ci[3]:.2f}%], 99% CI [{100 * ci[0]:.2f}%, {100 * ci[4]:.2f}%], "
          f"P(mean <= 0) = {(boot <= 0).mean():.4f}")
    json.dump({"ci95": [float(ci[1]), float(ci[3])], "ci99": [float(ci[0]), float(ci[4])], "median": float(ci[2]),
               "p_nonpositive": float((boot <= 0).mean()), "events": int(len(sums)), "trades": int(len(h))},
              open(out / "c3_r1_bootstrap.json", "w"), indent=1)

    # does requiring a later taker-buy print flatter the result?
    sig = s[(s["ask"] > 0.90) & (s["ask"] <= 0.97) & (s["days_to_end"] > 3) & (s["days_to_end"] <= 60) & s["holdout"]]
    first_sig = sig.sort_values("period").groupby("market_id").head(1)
    alt = first_sig.assign(ret=(first_sig["won"] - first_sig["ask"] - first_sig["fee_ps"]) / (first_sig["ask"] + first_sig["fee_ps"]))
    ra = mean_cluster(alt["ret"].to_numpy(), alt["cluster"].to_numpy())
    took = alt["market_id"].isin(h["market_id"])
    rb = mean_cluster(alt.loc[took, "ret"].to_numpy(), alt.loc[took, "cluster"].to_numpy())
    rc = mean_cluster(alt.loc[~took, "ret"].to_numpy(), alt.loc[~took, "cluster"].to_numpy())
    print(f"\nentry-print check (holdout): buying at the signal bar's ask, every first signal: "
          f"{100 * ra.mean:.2f}% (t={ra.t:.2f}, n={ra.n}); of those, markets where R1 later found a print: "
          f"{100 * rb.mean:.2f}% (n={rb.n}); where it did not: {100 * rc.mean:.2f}% (t={rc.t:.2f}, n={rc.n})")
    pd.DataFrame([{"entry": "signal-bar ask, all first signals", "ret%": 100 * ra.mean, "t": ra.t, "n": ra.n},
                  {"entry": "…markets R1 traded", "ret%": 100 * rb.mean, "t": rb.t, "n": rb.n},
                  {"entry": "…markets R1 could not enter", "ret%": 100 * rc.mean, "t": rc.t, "n": rc.n}]
                 ).to_csv(out / "c3_entry_print_check.csv", index=False)

    # ------------------------------------------------------------------ 4
    section("4. R1 as an account: $1,000 bankroll, finite capital (holdout period only)")
    # narrow topic tags ("themes"): the same definition the live risk manager uses
    tag_lists = meta.set_index("market_id")["tags"].fillna("").str.split("|")
    counts = tag_lists.explode().value_counts()
    limit = max(2, 0.03 * len(meta))
    from kht.trading.universe import is_operational_tag

    theme_set = {t for t in counts[(counts >= 2) & (counts <= limit)].index if t and not is_operational_tag(t)}
    themes_of = tag_lists.map(lambda tags: tuple(sorted(set(tags) & theme_set)))
    acct = []
    base_trades = h.drop(columns=["year", "half", "dte_bin", "px_bin", "outcome_side"]).copy()
    base_trades["themes"] = base_trades["market_id"].map(themes_of)
    for stake, max_event, max_theme in ((20, 20, None), (20, 20, 60), (20, 40, None), (50, 50, 150), (100, 100, 300)):
        for compound in (False,):
            r = run_portfolio(base_trades, Capital(bankroll=1000, stake=stake, max_event=max_event,
                                                   compound=compound, max_theme=max_theme))
            acct.append({"stake": stake, "max_event": max_event, "max_theme": max_theme, **r.stats})
            if stake == 20 and max_event == 20 and max_theme == 60:
                r.equity.assign(date=pd.to_datetime(r.equity["period"] * 86_400, unit="s")).to_csv(
                    out / "c4_r1_equity_stake20.csv", index=False)
                r.trades.to_csv(out / "c4_r1_account_trades_stake20.csv", index=False)
    acct = pd.DataFrame(acct)
    acct.to_csv(out / "c4_r1_account.csv", index=False)
    print(acct.round(3).to_string(index=False))

    # tail: worst events and worst days
    print("\nworst R1 holdout trades:")
    worst = h.sort_values("ret").head(12).merge(meta[["market_id", "question"]], on="market_id")
    print(worst[["question", "category", "entry_px", "ret", "dte_at_signal"]].round(3).to_string(index=False))
    worst.to_csv(out / "c4_r1_worst_trades.csv", index=False)
    losers = h[h["ret"] < -0.5]
    print(f"\nlosing trades (> 50% loss): {len(losers)} of {len(h)} ({100 * len(losers) / len(h):.2f}%); "
          f"max in one event: {losers.groupby('cluster').size().max() if len(losers) else 0}; "
          f"max resolving in one week: {losers.groupby(losers['exit_period'] // 7).size().max() if len(losers) else 0}")
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

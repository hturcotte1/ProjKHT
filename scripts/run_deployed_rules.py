"""Backtest the exact rules the two paper accounts run, on both samples.

These are *not* pre-registered: the main account's rule is the pre-registered
R1d trimmed to 95-98c and to stand-alone markets after the holdout had been
opened, and the experimental account's rule is a resting-bid variant. They are
reported so that the paper accounts can be compared with their own backtests,
not as independent evidence.

Usage: python scripts/run_deployed_rules.py [--out reports/research]
"""

from __future__ import annotations

import argparse
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


def stats(t: pd.DataFrame) -> dict:
    if len(t) < 20:
        return {"trades": len(t)}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    return {"trades": len(t), "events": int(t["cluster"].nunique()), "win%": 100 * float((t["proceeds"] > t["cost"]).mean()),
            "avg_entry": float(t["entry_px"].mean()), "avg_ret%": 100 * r.mean, "t_event": r.t,
            "med_hold_d": float(t["hold"].median()),
            "ret_per_30d%": 100 * float(t["ret"].sum() / max(t["hold"].clip(lower=1).sum(), 1) * 30)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/research")
    args = ap.parse_args()
    out = Path(args.out)
    meta = load_meta("closed")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    meta = meta[(~meta["category"].isin(["sports", "crypto"])) & (life >= 2) & resolved].copy()
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(build_trades_table(meta)), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    info = meta.set_index("market_id")
    single = ~info["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    dte_ok = ((s["days_to_end"] > 3) & (s["days_to_end"] <= 60)).to_numpy()

    def band(lo: float, hi: float) -> np.ndarray:
        return ((s["ask"] > lo) & (s["ask"] <= hi)).to_numpy() & dte_ok

    rules = {
        "main account: 95-98c, stand-alone, lift the ask": (Rule(0.95, 0.98, 3, 60), band(0.95, 0.98) & single),
        "  same band, legs of multi-outcome events (not traded)": (Rule(0.95, 0.98, 3, 60), band(0.95, 0.98) & ~single),
        "  same rule with a resting bid": (Rule(0.95, 0.98, 3, 60, entry="maker"), band(0.95, 0.98) & single),
        "experimental account: 90-98c, stand-alone, resting bid": (Rule(0.90, 0.98, 3, 60, entry="maker"), band(0.90, 0.98) & single),
        "  same band, lift the ask": (Rule(0.90, 0.98, 3, 60), band(0.90, 0.98) & single),
        "  90-95c only, stand-alone, lift the ask": (Rule(0.90, 0.95, 3, 60), band(0.90, 0.95) & single),
        "  90-95c only, stand-alone, resting bid": (Rule(0.90, 0.95, 3, 60, entry="maker"), band(0.90, 0.95) & single),
    }
    hold_of = s.groupby("market_id")["end_ts"].first() < SPLIT_TS
    rows, lists = [], {}
    for label, (rule, sig) in rules.items():
        t = candidate_trades(s, rule, signal=sig)
        t["holdout"] = t["market_id"].map(hold_of)
        lists[label] = t
        for name, mask in (("holdout", t["holdout"]), ("recent", ~t["holdout"]), ("all", np.ones(len(t), bool))):
            rows.append({"rule": label, "sample": name, **stats(t[mask])})
    res = pd.DataFrame(rows)
    res.to_csv(out / "d_deployed_rules.csv", index=False)
    for name in ("holdout", "recent", "all"):
        print(f"\n[{name}]\n", res[res["sample"] == name].drop(columns="sample").round(2).to_string(index=False))

    # the main account's rule as an account, over the whole history
    tag_lists = meta.set_index("market_id")["tags"].fillna("").str.split("|")
    counts = tag_lists.explode().value_counts()
    limit = max(2, 0.10 * len(meta))
    theme_set = {t for t in counts[(counts >= 2) & (counts <= limit)].index if t and not is_operational_tag(t)}
    themes_of = tag_lists.map(lambda tags: tuple(sorted(set(tags) & theme_set)))
    acct = []
    for label in ("main account: 95-98c, stand-alone, lift the ask", "experimental account: 90-98c, stand-alone, resting bid"):
        t = lists[label].copy()
        t["themes"] = t["market_id"].map(themes_of)
        for sample, mask in (("holdout", t["holdout"]), ("all", np.ones(len(t), bool))):
            r = run_portfolio(t[mask], Capital(bankroll=1000, stake=20, max_event=20, max_theme=80, max_exposure_frac=0.8))
            acct.append({"rule": label.split(":")[0], "sample": sample, **r.stats})
            if sample == "all":
                slug = "main" if label.startswith("main") else "experimental"
                r.equity.assign(date=pd.to_datetime(r.equity["period"] * 86_400, unit="s")).to_csv(
                    out / f"d_{slug}_equity.csv", index=False)
    acct = pd.DataFrame(acct)
    acct.to_csv(out / "d_deployed_accounts.csv", index=False)
    print("\nas $1,000 accounts ($20 a position, one per event, $80 per theme, 80% maximum exposure)\n",
          acct[["rule", "sample", "trades", "win_rate", "total_return", "cagr", "sharpe", "max_drawdown",
                "avg_utilisation", "years", "final_equity"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()

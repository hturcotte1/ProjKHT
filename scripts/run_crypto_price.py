"""Track C of the second round: the first round's rules on crypto price markets.

Crypto price markets were left out of the first round, so they are untouched
data. docs/04_second_round.md fixes what is run here before it was run:

    C1  the main paper account's rule exactly as configured (95-98c, not a leg
        of a multi-outcome event, 3-60 days to the scheduled end, bought at
        the next taker-buy print, held), and the pre-registered R1d (95-99c).
    QC  the quiet-favourite rule Q (90-98c, traded range of 3c or less over 7
        days) with its not-quiet control, and Q-long (60-365 days).

Standard errors are clustered by the calendar week of the scheduled end, all
coins together. The markets are split by scheduled end into a discovery set
(before 1 June 2026) and a holdout (from 1 June 2026); the holdout's tapes
are only read when --open-holdout is given.

    python scripts/run_crypto_price.py                 # discovery
    python scripts/run_crypto_price.py --open-holdout  # once, after its rules are committed
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_quiet_favourites as rq  # noqa: E402  (trailing_range, gap)

from kht.backtest.harvest import Rule, candidate_trades, prepare  # noqa: E402
from kht.data.download import load_meta  # noqa: E402
from kht.research.crypto import parse_question  # noqa: E402
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes  # noqa: E402
from kht.research.sports import build_trades_table  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
SPLIT_TS = pd.Timestamp("2026-06-01", tz="UTC").timestamp()
WEEK = 7 * 86_400


def crypto_price_meta() -> pd.DataFrame:
    """Resolved crypto price markets with a question this project can read."""
    meta = load_meta("closed")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    q = meta["question"].str.lower()
    price_q = q.str.contains(r"\b(?:above|below|greater than|less than|between|hit|reach|dip to|fall to|drop to)\b")
    meta = meta[(meta["category"] == "crypto") & ~q.str.contains("up or down") & price_q & (life >= 2) & resolved].copy()
    parsed = meta["question"].map(parse_question)
    meta["coin"] = parsed.map(lambda p: p.coin if p else None)
    meta["kind"] = parsed.map(lambda p: p.kind if p else None)
    meta["strike"] = parsed.map(lambda p: p.strike if p else np.nan)
    meta["strike_hi"] = parsed.map(lambda p: p.strike_hi if p and p.strike_hi else np.nan)
    return meta


def panel(meta: pd.DataFrame) -> pd.DataFrame:
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(build_trades_table(meta)), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    end = s["end_ts"].fillna(s["closed_ts"])                       # a market with no scheduled end never signals
    s["cluster"] = (end // WEEK).astype(np.int64)                  # one week of scheduled ends = one bet
    return s


def stats(t: pd.DataFrame) -> dict:
    if len(t) < 20:
        return {"trades": len(t), "lost": int((t["won"] == 0).sum()) if len(t) else 0}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    return {"trades": len(t), "weeks": int(t["cluster"].nunique()), "win%": 100 * float((t["proceeds"] > t["cost"]).mean()),
            "lost": int((t["won"] == 0).sum()), "weeks_with_a_loss": int(t.loc[t["won"] == 0, "cluster"].nunique()),
            "avg_cost": float(t["cost"].mean()), "avg_ret%": 100 * r.mean, "se%": 100 * r.se, "t_week": r.t,
            "med_dte": float(t["dte_at_signal"].median())}


def loss_count_p(q: pd.DataFrame, control: pd.DataFrame) -> float:
    """One-sided exact p: clusters with a losing Q trade, against the control's loss rate per trade."""
    if not len(q) or not len(control):
        return float("nan")
    p0 = float((control["won"] == 0).mean())
    n = int(q["cluster"].nunique())
    k = int(q.loc[q["won"] == 0, "cluster"].nunique())
    return float(binom.cdf(k, n, p0))


def verdict(label: str, q: pd.DataFrame, control: pd.DataFrame) -> None:
    print("-" * 110)
    if len(q) < 20:
        print(f"{label}: only {len(q)} trades; no verdict")
        return
    r = mean_cluster(q["ret"].to_numpy(), q["cluster"].to_numpy())
    d, t_d = rq.gap(q, control) if len(control) >= 20 else (float("nan"), float("nan"))
    p = loss_count_p(q, control)
    ok = r.mean > 0 and abs(r.t) >= 3 and d > 0 and abs(t_d) >= 2 and p < 0.01
    print(f"{label}: {len(q):,} trades in {q['cluster'].nunique()} weeks, {int((q['won'] == 0).sum())} lost in "
          f"{q.loc[q['won'] == 0, 'cluster'].nunique()} weeks; return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f})")
    if len(control):
        rc = mean_cluster(control["ret"].to_numpy(), control["cluster"].to_numpy())
        print(f"  control: {len(control):,} trades, {int((control['won'] == 0).sum())} lost ({100 * (control['won'] == 0).mean():.2f}%); "
              f"return per trade {100 * rc.mean:+.2f}% (t = {rc.t:.2f})")
    print(f"  Q minus control {100 * d:+.2f} points (t = {t_d:.2f}); exact p for the count of losing weeks {p:.4f}")
    print(f"  bar (positive with |t| >= 3; above control with |t| >= 2; exact p < 0.01)  ->  {'PASSED' if ok else 'NOT PASSED'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--open-holdout", action="store_true", help="read the holdout (scheduled end from 1 June 2026)")
    args = ap.parse_args()
    name = "holdout" if args.open_holdout else "discovery"

    meta = crypto_price_meta()
    print(f"crypto price markets: {len(meta):,}; questions read: {int(meta['kind'].notna().sum()):,} "
          f"({meta['kind'].value_counts().to_dict()}); not read: {int(meta['kind'].isna().sum())}")
    meta = meta[meta["kind"].notna()]
    hold = meta["end_ts"] >= SPLIT_TS
    print(f"discovery (scheduled end before 2026-06-01): {int((~hold).sum()):,} markets; holdout: {int(hold.sum()):,}")
    meta = meta[hold] if args.open_holdout else meta[~hold]
    print(f"\n=== {name.upper()} SET: {len(meta):,} markets, scheduled ends "
          f"{pd.to_datetime(meta.end_ts.min(), unit='s').date()} to {pd.to_datetime(meta.end_ts.max(), unit='s').date()} ===")

    s = panel(meta)
    info = meta.set_index("market_id")
    single = ~info["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    kind = info["kind"].reindex(s["market_id"]).to_numpy()
    coin = info["coin"].reindex(s["market_id"]).to_numpy()
    ask = s["ask"].to_numpy()
    dte = s["days_to_end"].to_numpy()
    print(f"panel: {len(s):,} outcome-days in {s['market_id'].nunique():,} markets, {s['cluster'].nunique()} weeks of scheduled ends")

    def band(lo: float, hi: float, dlo: float = 3, dhi: float = 60) -> np.ndarray:
        return (ask > lo) & (ask <= hi) & (dte > dlo) & (dte <= dhi)

    def trades(rule: Rule, signal: np.ndarray) -> pd.DataFrame:
        t = candidate_trades(s, rule, signal=signal)
        if len(t):
            t["kind"] = t["market_id"].map(info["kind"]).to_numpy()
            t["coin"] = t["market_id"].map(info["coin"]).to_numpy()
            t["year"] = pd.to_datetime(t["entry_period"], unit="D").dt.year
        return t

    rows = []

    def report(label: str, t: pd.DataFrame) -> pd.DataFrame:
        rows.append({"rule": label, "sample": name, **stats(t)})
        return t

    # ------------------------------------------------------------------ C1
    c1 = report("C1: main account's rule, 95-98c, not a leg", trades(Rule(0.95, 0.98, 3, 60), band(0.95, 0.98) & single))
    r1d = report("    R1d as pre-registered, 95-99c, legs included", trades(Rule(0.95, 0.99, 3, 60), band(0.95, 0.99)))
    report("    control: long shots 3-10c", trades(Rule(0.03, 0.10, 3, 60), band(0.03, 0.10)))
    report("    control: coin flips 40-60c", trades(Rule(0.40, 0.60, 3, 60), band(0.40, 0.60)))
    report("    90-95c, not a leg", trades(Rule(0.90, 0.95, 3, 60), band(0.90, 0.95) & single))
    for k in ("above", "below", "reach", "dip"):
        report(f"    C1 by kind: {k}", trades(Rule(0.95, 0.98, 3, 60), band(0.95, 0.98) & single & (kind == k)))
    for c in ("bitcoin", "ethereum", "solana", "xrp"):
        report(f"    C1 by coin: {c}", trades(Rule(0.95, 0.98, 3, 60), band(0.95, 0.98) & single & (coin == c)))
    # shorter-dated: most of these markets live a week, so 3-60 days sees little of them
    report("    95-98c, not a leg, 1-3 days to the end (not pre-registered)", trades(Rule(0.95, 0.98, 1, 3), band(0.95, 0.98, 1, 3) & single))
    print("-" * 110)
    if len(c1) >= 20:
        r = mean_cluster(c1["ret"].to_numpy(), c1["cluster"].to_numpy())
        print(f"C1 on the {name} set: {len(c1):,} trades in {c1['cluster'].nunique()} weeks, {int((c1['won'] == 0).sum())} lost; "
              f"return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f})  ->  "
              f"{'REPLICATES' if r.mean > 0 and abs(r.t) >= 3 else 'DOES NOT REPLICATE'} at |t| >= 3")
    c1.to_csv(OUT / f"cp_trades_C1_{name}.csv", index=False)

    # ------------------------------------------------------------------ QC
    rng7, seasoned7 = rq.trailing_range(s, 7)
    quiet = seasoned7 & (rng7 <= 0.03 + 1e-9)
    rule_q = Rule(0.90, 0.98, 3, 60)
    q = report("QC: quiet, 90-98c, not a leg, 3-60 days", trades(rule_q, band(0.90, 0.98) & single & quiet))
    qc = report("    control: not quiet", trades(rule_q, band(0.90, 0.98) & single & ~quiet))
    rule_long = Rule(0.90, 0.98, 60, 365)
    ql = report("Q-long: quiet, 90-98c, not a leg, 60-365 days", trades(rule_long, band(0.90, 0.98, 60, 365) & single & quiet))
    qlc = report("    control: not quiet", trades(rule_long, band(0.90, 0.98, 60, 365) & single & ~quiet))
    verdict(f"QC on the {name} set", q, qc)
    verdict(f"Q-long on the {name} set", ql, qlc)
    q.to_csv(OUT / f"cp_trades_QC_{name}.csv", index=False)

    res = pd.DataFrame(rows)
    res.to_csv(OUT / f"cp_rules_{name}.csv", index=False)
    print("\n", res.round(2).to_string(index=False))

    # what a contract went on to earn by the price paid, every outcome-day (as in the first round's table)
    cal = s[(dte > 3) & (dte <= 60) & single & np.isfinite(ask)].copy()
    cal["band"] = pd.cut(cal["ask"], [0.0, 0.03, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 0.90, 0.95, 0.97, 0.99, 1.0])
    out = []
    for b, g in cal.groupby("band", observed=True):
        r = mean_cluster(g["net_ps"].to_numpy(), g["cluster"].to_numpy())
        out.append({"price paid": str(b), "outcome-days": len(g), "markets": g["market_id"].nunique(), "won%": 100 * g["won"].mean(),
                    "avg ask": 100 * g["ask"].mean(), "profit per share, cents": 100 * r.mean, "t_week": r.t})
    cal_t = pd.DataFrame(out)
    cal_t.to_csv(OUT / f"cp_calibration_{name}.csv", index=False)
    print("\nby price paid, not a leg, 3-60 days to the end, every outcome-day:\n", cal_t.round(2).to_string(index=False))


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
    holdout = "--open-holdout" in sys.argv
    with (OUT / f"crypto_price_{'holdout' if holdout else 'discovery'}_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__

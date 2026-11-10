"""Second round: the quiet-favourite rule Q on a universe it has never seen.

docs/04_second_round.md (section 5) fixes the rule, its control and the bar
before any tape of these markets was read.

    Q       ask above 90c and at most 98c; scheduled end more than 3 and at
            most 60 days away; the outcome's traded range over the last 7 days
            is 3c or less and the market was already in the panel 7 days ago.
            Bought at the next taker-buy print within 3 days if above 90c and
            at most 98.5c; today's fee; held to resolution; one per market.
    control the same band, horizon and entry on the first day not quiet.
    Q-long  the same with the scheduled end 60 to 365 days away.
    bar     Q positive with |t| >= 3 (clustered by event); above its control
            with |t| >= 2; and fewer events with a losing Q trade than the
            control's loss rate would produce (one-sided exact p < 0.01).

Universe QS: resolved sports markets that are not single games (season-long,
tournament and similar questions), 100,000 shares or more, a life of 14 days
or more. Legs of multi-outcome events and stand-alone markets are both
traded and reported separately.

    python scripts/run_quiet_replication.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_quiet_favourites as rq  # noqa: E402

from kht.backtest.harvest import Rule, candidate_trades, prepare  # noqa: E402
from kht.data.download import load_meta  # noqa: E402
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes  # noqa: E402
from kht.research.sports import build_trades_table  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"


def sports_other_meta() -> pd.DataFrame:
    meta = load_meta("closed")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    not_game = ~meta["is_game"].fillna(False).astype(bool) & meta["game_start_ts"].isna()
    return meta[(meta["category"] == "sports") & not_game & (life >= 14) & resolved].copy()


def stats(t: pd.DataFrame) -> dict:
    if len(t) < 20:
        return {"trades": len(t), "lost": int((t["won"] == 0).sum()) if len(t) else 0}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    return {"trades": len(t), "events": int(t["cluster"].nunique()), "win%": 100 * float((t["proceeds"] > t["cost"]).mean()),
            "lost": int((t["won"] == 0).sum()), "events_with_a_loss": int(t.loc[t["won"] == 0, "cluster"].nunique()),
            "avg_cost": float(t["cost"].mean()), "avg_ret%": 100 * r.mean, "se%": 100 * r.se, "t_event": r.t,
            "med_dte": float(t["dte_at_signal"].median()), "med_hold_d": float(t["hold"].median())}


def loss_count_p(q: pd.DataFrame, control: pd.DataFrame) -> float:
    """One-sided exact p: events with a losing Q trade, against the control's loss rate per trade."""
    if not len(q) or not len(control):
        return float("nan")
    return float(binom.cdf(int(q.loc[q["won"] == 0, "cluster"].nunique()), int(q["cluster"].nunique()), float((control["won"] == 0).mean())))


def verdict(label: str, q: pd.DataFrame, control: pd.DataFrame) -> None:
    print("-" * 110)
    if len(q) < 20:
        print(f"{label}: only {len(q)} trades; no verdict")
        return
    r = mean_cluster(q["ret"].to_numpy(), q["cluster"].to_numpy())
    rc = mean_cluster(control["ret"].to_numpy(), control["cluster"].to_numpy())
    d, t_d = rq.gap(q, control)
    p = loss_count_p(q, control)
    ok = r.mean > 0 and abs(r.t) >= 3 and d > 0 and abs(t_d) >= 2 and p < 0.01
    print(f"{label}: {len(q):,} trades in {q['cluster'].nunique():,} events, {int((q['won'] == 0).sum())} lost in "
          f"{q.loc[q['won'] == 0, 'cluster'].nunique()} events ({100 * (q['won'] == 0).mean():.2f}%); "
          f"return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f})")
    print(f"  control: {len(control):,} trades, {int((control['won'] == 0).sum())} lost ({100 * (control['won'] == 0).mean():.2f}%); "
          f"return per trade {100 * rc.mean:+.2f}% (t = {rc.t:.2f})")
    print(f"  Q minus control {100 * d:+.2f} points (t = {t_d:.2f}); exact p for the count of losing events {p:.5f}")
    print(f"  bar (positive with |t| >= 3; above control with |t| >= 2; exact p < 0.01)  ->  {'PASSED' if ok else 'NOT PASSED'}")


def main() -> None:
    meta = sports_other_meta()
    have = {p.stem for p in (ROOT / "data" / "trades").glob("*.parquet")}
    print(f"sports markets that are not single games: {len(meta):,}; tapes on disk: {int(meta['condition_id'].isin(have).sum()):,}")
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(build_trades_table(meta)), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    print(f"panel: {len(s):,} outcome-days in {s['market_id'].nunique():,} markets, {s['cluster'].nunique():,} events, "
          f"{pd.to_datetime(s.ts.min(), unit='s').date()} to {pd.to_datetime(s.ts.max(), unit='s').date()}")
    single = ~meta.set_index("market_id")["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    ask = s["ask"].to_numpy()
    dte = s["days_to_end"].to_numpy()
    rng7, seasoned7 = rq.trailing_range(s, 7)
    quiet = seasoned7 & (rng7 <= 0.03 + 1e-9)

    def band(lo: float, hi: float, dlo: float, dhi: float) -> np.ndarray:
        return (ask > lo) & (ask <= hi) & (dte > dlo) & (dte <= dhi)

    def trades(rule: Rule, signal: np.ndarray) -> pd.DataFrame:
        t = candidate_trades(s, rule, signal=signal)
        if len(t):
            t["single"] = t["market_id"].map(~meta.set_index("market_id")["neg_risk"].fillna(False).astype(bool)).to_numpy()
            t["year"] = pd.to_datetime(t["entry_period"], unit="D").dt.year
        return t

    rows = []

    def report(label: str, t: pd.DataFrame) -> pd.DataFrame:
        rows.append({"rule": label, **stats(t)})
        return t

    rule_q, rule_long = Rule(0.90, 0.98, 3, 60), Rule(0.90, 0.98, 60, 365)
    q = report("Q: quiet, 90-98c, 3-60 days", trades(rule_q, band(0.90, 0.98, 3, 60) & quiet))
    qc = report("   control: not quiet", trades(rule_q, band(0.90, 0.98, 3, 60) & ~quiet))
    ql = report("Q-long: quiet, 90-98c, 60-365 days", trades(rule_long, band(0.90, 0.98, 60, 365) & quiet))
    qlc = report("   control: not quiet", trades(rule_long, band(0.90, 0.98, 60, 365) & ~quiet))
    print("=" * 110)
    print("THE PRE-REGISTERED REPLICATION (sports markets that are not single games)")
    verdict("Q", q, qc)
    verdict("Q-long", ql, qlc)
    print("=" * 110)
    q.to_csv(OUT / "qs_trades_Q.csv", index=False)
    qc.to_csv(OUT / "qs_trades_Q_control.csv", index=False)
    ql.to_csv(OUT / "qs_trades_Qlong.csv", index=False)

    # reported alongside
    for label, mask in (("stand-alone", single), ("legs of multi-outcome events", ~single)):
        report(f"Q, {label}", trades(rule_q, band(0.90, 0.98, 3, 60) & quiet & mask))
        report(f"   control, {label}", trades(rule_q, band(0.90, 0.98, 3, 60) & ~quiet & mask))
        report(f"Q-long, {label}", trades(rule_long, band(0.90, 0.98, 60, 365) & quiet & mask))
        report(f"   control, {label}", trades(rule_long, band(0.90, 0.98, 60, 365) & ~quiet & mask))
    for lo, hi in ((0.90, 0.95), (0.95, 0.98)):
        report(f"Q, {lo:.2f}-{hi:.2f} only", trades(Rule(lo, hi, 3, 60), band(lo, hi, 3, 60) & quiet))
        report(f"   control, {lo:.2f}-{hi:.2f} only", trades(Rule(lo, hi, 3, 60), band(lo, hi, 3, 60) & ~quiet))
    report("first round's main rule as configured: 95-98c, stand-alone, 3-60 days", trades(Rule(0.95, 0.98, 3, 60), band(0.95, 0.98, 3, 60) & single))
    report("first round's R1d: 95-99c, legs included, 3-60 days", trades(Rule(0.95, 0.99, 3, 60), band(0.95, 0.99, 3, 60)))
    report("long shots 3-10c, 3-60 days", trades(Rule(0.03, 0.10, 3, 60), band(0.03, 0.10, 3, 60)))
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "qs_quiet_replication.csv", index=False)
    print("\n", res.round(2).to_string(index=False))

    for name, t in (("Q", q), ("Q-long", ql)):
        if len(t):
            print(f"\n{name} by year of entry:")
            print(t.groupby("year").agg(trades=("won", "size"), lost=("won", lambda w: int((w == 0).sum())),
                                        avg_ret_pct=("ret", lambda r: 100 * r.mean())).round(2).to_string())
            lost = t[t["won"] == 0].copy()
            if len(lost):
                lost["entry"] = pd.to_datetime(lost["entry_period"], unit="D").dt.date
                lost["question"] = lost["market_id"].map(meta.set_index("market_id")["question"]).str.slice(0, 90)
                print(f"{name} losing trades:\n", lost[["entry", "entry_px", "dte_at_signal", "question"]].to_string(index=False))


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
    with (OUT / "quiet_replication_sports_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__

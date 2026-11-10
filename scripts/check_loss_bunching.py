"""How did the losing trades of the rule that passed bunch together?

A rule that wins 98 times in 100 and loses the whole stake otherwise lives or
dies by whether its losses arrive one at a time or together. This reads the
trade list of the pre-registered rule R1d (buy 95-99c, hold to resolution;
holdout and newer sample together) and counts losses by event, by week and by
month. Nothing is fitted and nothing is chosen: it is a description of trades
that already exist in reports/research/c2_trades_R1d.csv.

Written after the test, so it is exploratory. It cannot show the thing that
matters most, which is a shock the three years do not contain.

    python scripts/check_loss_bunching.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for s in self.streams:
            s.write(text)

    def flush(self):
        for s in self.streams:
            s.flush()


def worst_window(days: np.ndarray, events: np.ndarray, width: int) -> tuple[int, int, int]:
    """Most separate losing events in any `width`-day window: (events, trades, first day)."""
    best = (0, 0, -1)
    for i in range(len(days)):
        j = int(np.searchsorted(days, days[i] + width, side="left"))
        found = (len(set(events[i:j])), j - i, int(days[i]))
        if found[:2] > best[:2]:
            best = found
    return best


def main() -> None:
    t = pd.read_csv(OUT / "c2_trades_R1d.csv")
    t["exit_date"] = pd.to_datetime(t["exit_period"].astype(int), unit="D")
    t["month"] = t["exit_date"].dt.to_period("M").astype(str)
    t["lost"] = (t["won"] == 0).astype(int)
    lose = t[t["lost"] == 1].sort_values("exit_period")

    n, k = len(t), len(lose)
    # Per share a win pays (1 - cost) and a loss costs `cost`, so the loss rate
    # q that leaves nothing solves (1 - q)(1 - cost) = q * cost: q = 1 - cost.
    breakeven_loss = 1.0 - float(t["cost"].mean())
    print(f"R1d, holdout and newer sample: {n:,} trades, {k} lost ({k / n:.2%}); exits {t.exit_date.min().date()} to {t.exit_date.max().date()}")
    print(f"average cost per share {t.cost.mean():.4f}, so the rule breaks even at a loss rate of {breakeven_loss:.2%}")

    per_event = lose["cluster"].value_counts()
    print(f"\nthe {k} losing trades came from {per_event.size} separate events; the most from any one event is {int(per_event.max())}")

    days = lose["exit_period"].to_numpy().astype(int)
    events = lose["cluster"].to_numpy()
    rows = []
    for width in (7, 30):
        ev, tr, first = worst_window(days, events, width)
        start = pd.Timestamp(first, unit="D").date()
        in_window = t[(t.exit_period >= first) & (t.exit_period < first + width)]
        cats = ", ".join(sorted(in_window[in_window.lost == 1]["category"]))
        print(f"worst {width}-day window: {tr} losing trades in {ev} separate events, from {start}, "
              f"out of {len(in_window)} trades that ended in it ({cats})")
        rows.append({"window_days": width, "from": str(start), "losing_trades": tr, "separate_losing_events": ev,
                     "trades_ending_in_window": len(in_window), "categories_of_losers": cats})
    pd.DataFrame(rows).to_csv(OUT / "c6_r1d_worst_windows.csv", index=False)

    m = t.groupby("month").agg(trades=("lost", "size"), losing_trades=("lost", "sum"),
                               avg_ret_pct=("ret", lambda s: 100 * s.mean()))
    m["separate_losing_events"] = lose.groupby("month")["cluster"].nunique().reindex(m.index).fillna(0).astype(int)
    m["loss_rate_pct"] = 100 * m["losing_trades"] / m["trades"]
    m = m[["trades", "losing_trades", "separate_losing_events", "loss_rate_pct", "avg_ret_pct"]].round(2)
    m.to_csv(OUT / "c6_r1d_losses_by_month.csv")

    print(f"\n{len(m)} months:")
    for label, sel in [("no losing trade", m.losing_trades == 0), ("1 or 2", m.losing_trades.between(1, 2)),
                       ("3 or 4", m.losing_trades.between(3, 4)), ("5 or more", m.losing_trades >= 5)]:
        print(f"  {label:16s} {int(sel.sum()):3d}")
    down = m[m.avg_ret_pct < 0]
    print(f"months in which the average trade lost money: {len(down)} of {len(m)}")
    print(f"longest run of such months in a row: {longest_run((m.avg_ret_pct < 0).to_numpy())}")
    print("\nthe six worst months by average return per trade:")
    print(m.sort_values("avg_ret_pct").head(6).to_string())

    bunching_test(t)

    c = t.groupby("category").agg(trades=("lost", "size"), losing_trades=("lost", "sum"),
                                  avg_ret_pct=("ret", lambda s: 100 * s.mean()))
    c["loss_rate_pct"] = 100 * c["losing_trades"] / c["trades"]
    c = c.sort_values("trades", ascending=False).round(2)
    c.to_csv(OUT / "c6_r1d_losses_by_category.csv")
    print("\nby category:")
    print(c.to_string())


def bunching_test(t: pd.DataFrame, draws: int = 5000, seed: int = 7) -> None:
    """Do the losses of separate events bunch in time more than chance would produce?

    Dealing the losses out at random over the trades would be the wrong
    comparison, because when a trade ends depends on whether it lost: winners
    mostly end on their deadline, hundreds on the same day at a quarter end,
    while a loser ends whenever its event happens. So the comparison is made in
    calendar time. Each event is at risk on every day the rule held it, and
    under the null a loss is equally likely on any event-day. The observed loss
    days are compared with the same number of days drawn at random in
    proportion to how many events were held that day.

    Events, not trades: two trades in one event lose together by construction,
    and that exposure is capped separately.
    """
    rng = np.random.default_rng(seed)
    ev = t.groupby("cluster").agg(first=("entry_period", "min"), last=("exit_period", "max"), lost=("lost", "max"))
    loss_day = t[t["lost"] == 1].groupby("cluster")["exit_period"].min().to_numpy().astype(int)
    d0, d1 = int(ev["first"].min()), int(ev["last"].max())
    held = np.zeros(d1 - d0 + 2)
    np.add.at(held, ev["first"].to_numpy().astype(int) - d0, 1)
    np.add.at(held, ev["last"].to_numpy().astype(int) - d0 + 1, -1)
    held = np.cumsum(held)[:-1]                       # events held on each day
    p_day = held / held.sum()
    days = np.arange(d0, d1 + 1)
    month = pd.factorize(pd.to_datetime(days, unit="D").to_period("M"))[0]
    k = len(loss_day)
    expected = k * np.bincount(month, weights=p_day)

    def most_within(sample: np.ndarray, width: int) -> int:
        d = np.sort(sample)
        return int((np.searchsorted(d, d + width, side="left") - np.arange(len(d))).max())

    def measures(sample: np.ndarray) -> tuple[float, int, int]:
        got = np.bincount(month[sample - d0], minlength=len(expected))
        keep = expected > 0
        return float(((got[keep] - expected[keep]) ** 2 / expected[keep]).sum()), most_within(sample, 7), most_within(sample, 30)

    seen = measures(loss_day)
    sims = np.array([measures(rng.choice(days, size=k, p=p_day)) for _ in range(draws)])
    names = ["spread of losing events across months (chi-square)", "most losing events in any 7 days",
             "most losing events in any 30 days"]
    print(f"\ndo losses bunch in time more than chance? {k} losing events, {len(ev):,} events held, "
          f"{held.mean():.0f} at a time on average; {draws:,} random draws")
    rows = []
    for j, name in enumerate(names):
        p_value = float((sims[:, j] >= seen[j]).mean())
        print(f"  {name}: {seen[j]:.1f}; by chance {np.median(sims[:, j]):.1f}, "
              f"95% of draws at or below {np.quantile(sims[:, j], 0.95):.1f}; p = {p_value:.2f}")
        rows.append({"measure": name, "observed": round(float(seen[j]), 2),
                     "median_by_chance": round(float(np.median(sims[:, j])), 2),
                     "p95_by_chance": round(float(np.quantile(sims[:, j], 0.95)), 2), "p_value": round(p_value, 4)})
    pd.DataFrame(rows).to_csv(OUT / "c6_r1d_bunching_test.csv", index=False)

    busiest = t.groupby("exit_period").size().sort_values(ascending=False).head(10)
    on_busiest = int(t[t["lost"] == 1]["exit_period"].isin(busiest.index).sum())
    print(f"  the 10 busiest exit days hold {busiest.sum() / len(t):.0%} of all trades and "
          f"{on_busiest} of the {int(t['lost'].sum())} losing ones: deadlines are not where the losses are")


def longest_run(flags: np.ndarray) -> int:
    best = run = 0
    for f in flags:
        run = run + 1 if f else 0
        best = max(best, run)
    return best


if __name__ == "__main__":
    with (OUT / "loss_bunching_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        main()
        sys.stdout = sys.__stdout__

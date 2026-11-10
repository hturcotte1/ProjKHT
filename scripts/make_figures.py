"""Draw the research figures from the result tables.

Usage: python scripts/make_figures.py [--tables reports/research] [--out reports/figures]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from kht.research import plots as P


def price_labels(intervals: pd.Series) -> list[str]:
    out = []
    for s in intervals:
        lo, hi = s.strip("(]").split(", ")
        out.append(f"{float(lo) * 100:g}–{float(hi) * 100:g}")
    return out


def fig_calibration(tables: Path, out: Path) -> None:
    c = pd.read_csv(tables / "c1_calibration_by_price.csv")
    for sample, name in (("holdout", "calibration_holdout.png"), ("discovery", "calibration_recent.png")):
        g = c[c["sample"] == sample]
        if g.empty:
            continue
        fig, ax = P.new_figure(8.6, 4.3)
        P.signed_bars(ax, price_labels(g["ask"]), list(g["net_c"]))
        ax.set_ylabel("profit per share (cents)")
        ax.set_xlabel("price paid (cents)")
        which = "markets scheduled to end before May 2026" if sample == "holdout" else "markets scheduled to end from May 2026"
        P.title(ax, "Cheap contracts lose, expensive contracts win",
                f"Bought at the ask and held to resolution, after today's fees; {which}")
        P.save(fig, out / name)


def fig_equity(tables: Path, out: Path) -> None:
    path = tables / "c4_r1_equity_stake20.csv"
    if not path.exists():
        return
    e = pd.read_csv(path, parse_dates=["date"])
    fig, ax = P.new_figure(8.6, 3.9)
    ax.plot(e["date"], e["equity"], color=P.BLUE, linewidth=2, solid_capstyle="round", solid_joinstyle="round", zorder=3)
    ax.fill_between(e["date"], e["equity"].min() - 5, e["equity"], color=P.BLUE, alpha=0.10, zorder=2, linewidth=0)
    last = e.iloc[-1]
    ax.scatter([last["date"]], [last["equity"]], s=42, color=P.BLUE, edgecolor=P.SURFACE, linewidth=2, zorder=4)
    ax.annotate(f"${last['equity']:,.0f}", (last["date"], last["equity"]), xytext=(-8, 8), textcoords="offset points",
                ha="right", fontsize=9.5, color=P.INK)
    ax.axhline(1000, color=P.INK_3, linewidth=1.0, zorder=1)
    ax.set_ylabel("account value ($)")
    ax.set_ylim(e["equity"].min() - 5, e["equity"].max() + 12)
    P.title(ax, "Rule R1 as a $1,000 account on the holdout",
            "$20 per position, one position per event, positions carried at cost until they resolve")
    P.save(fig, out / "r1_equity_holdout.png")


def fig_roundtrips(tables: Path, out: Path) -> None:
    path = tables / "x_a3_roundtrip_trades.csv"
    if not path.exists():
        return
    a = pd.read_csv(path)
    keep = [("buy what fell >= 10c, hold 1d", "fell ≥10¢\n1 day"), ("buy what rose >= 10c, hold 1d", "rose ≥10¢\n1 day"),
            ("buy what fell >= 10c, hold 3d", "fell ≥10¢\n3 days"), ("buy what rose >= 10c, hold 3d", "rose ≥10¢\n3 days"),
            ("buy what fell >= 20c, hold 3d", "fell ≥20¢\n3 days"), ("buy what rose >= 20c, hold 3d", "rose ≥20¢\n3 days"),
            ("benchmark: no move, hold 3d (cost of a round trip)", "no signal\n3 days")]
    rows = [(lab, float(a.loc[a["rule"] == key, "avg_ret%"].iloc[0])) for key, lab in keep if (a["rule"] == key).any()]
    if not rows:
        return
    fig, ax = P.new_figure(8.6, 4.3)
    colors = [P.NEUTRAL if "no signal" in lab else None for lab, _ in rows]
    labels, values = [r[0] for r in rows], [r[1] for r in rows]
    P.signed_bars(ax, labels, values, value_fmt="{:+.1f}%")
    # the benchmark bar is context, not a strategy: repaint it neutral
    for patch, col in zip([p for p in ax.patches], colors):
        if col:
            patch.set_facecolor(col)
    ax.set_ylabel("average return per trade")
    P.percent_axis(ax, step=5)
    P.title(ax, "Buying yesterday's movers and selling a few days later loses money",
            "Buy at the ask one day after the move, sell at the bid, fees both ways; the grey bar is the cost of any round trip")
    P.save(fig, out / "roundtrip_perception_trades.png")


def fig_walkforward(tables: Path, out: Path) -> None:
    path = tables / "m_walkforward_by_predicted_edge.csv"
    if not path.exists():
        return
    w = pd.read_csv(path)
    fig, ax = P.new_figure(6.4, 3.9)
    P.signed_bars(ax, [str(x) for x in w["predicted edge"]], list(w["avg ret %"]), value_fmt="{:+.1f}%")
    ax.set_ylabel("realised return per trade")
    ax.set_xlabel("model's predicted edge, out of sample")
    P.percent_axis(ax)
    P.title(ax, "Does a bigger predicted edge mean a bigger result?",
            "Model refitted each quarter on resolved trades only, scored on the next quarter")
    P.save(fig, out / "model_walkforward.png")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", default="reports/research")
    ap.add_argument("--out", default="reports/figures")
    args = ap.parse_args()
    tables, out = Path(args.tables), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for fn in (fig_calibration, fig_equity, fig_roundtrips, fig_walkforward):
        try:
            fn(tables, out)
        except FileNotFoundError as exc:
            print(f"skipped {fn.__name__}: {exc}")
    print("figures:", sorted(p.name for p in out.glob("*.png")))


if __name__ == "__main__":
    main()

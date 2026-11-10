"""Human-readable status of a (paper or live) account, as Markdown."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as fh:
        return list(csv.DictReader(fh))


def _when(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(ts))


def _span(seconds: float) -> str:
    hours = seconds / 3600
    if hours < 1:
        return f"{round(seconds / 60)} minutes"
    return f"{hours:.1f} hours" if hours < 48 else f"{hours / 24:.1f} days"


def _count_decisions(path: Path, action: str) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open() as fh:
        for line in fh:
            if f'"{action}"' not in line:
                continue
            try:
                n += json.loads(line).get("action") == action
            except ValueError:
                continue
    return n


def build_report(state_dir: str | Path) -> str:
    d = Path(state_dir)
    state_path = d / "state.json"
    if not state_path.exists():
        return "No state yet: run a cycle first.\n"
    st: dict[str, Any] = json.loads(state_path.read_text())
    pf = st["portfolio"]
    names = st.get("market_names", {})
    marks = st.get("marks", {})
    limits = st.get("limits", {})
    bankroll = float(limits.get("bankroll", 0.0))
    equity_rows = _read_csv(d / "equity.csv")
    fills = _read_csv(d / "fills.csv")
    settlements = _read_csv(d / "settlements.csv")

    positions = pf.get("positions", {})
    value = sum(p["shares"] * marks.get(tok, p["cost"] / p["shares"] if p["shares"] else 0.0)
                for tok, p in positions.items())
    equity = pf["cash"] + value
    now = time.time()
    lines = [
        f"# Account status ({st.get('mode', 'paper')})",
        "",
        f"As of {_when(st.get('saved_ts', now))}. Started {_when(st.get('started_ts', now))}.",
        "",
        "| | |",
        "|---|---|",
        f"| Equity (positions marked at the bid) | ${equity:,.2f} |",
        f"| Starting bankroll | ${bankroll:,.2f} |",
        f"| Change | ${equity - bankroll:+,.2f} ({(equity / bankroll - 1) * 100 if bankroll else 0:+.2f}%) |",
        f"| Cash | ${pf['cash']:,.2f} |",
        f"| In positions (cost) | ${sum(p['cost'] for p in positions.values()):,.2f} |",
        f"| Realised profit | ${pf.get('realized', 0.0):+,.2f} |",
        f"| Fees paid | ${pf.get('fees_paid', 0.0):,.2f} |",
        f"| Open positions | {len(positions)} |",
        f"| Fills | {pf.get('n_fills', 0)} |",
        f"| Settled positions | {len(settlements)} |",
    ]
    risk = st.get("risk", {})
    if risk.get("halted"):
        lines += ["", f"**Trading is halted:** {risk.get('halt_reason', '')}"]
    gaps = _count_decisions(d / "decisions.jsonl", "tape_incomplete")
    if gaps:
        lines += ["", f"**Fills may be missing:** {gaps} time{'s' if gaps != 1 else ''} the trades in a market with a "
                      "resting order could not be read back to the previous cycle (`tape_incomplete` in `decisions.jsonl`)."]

    if positions:
        lines += ["", "## Open positions", "",
                  "| Market | Holding | Shares | Avg cost | Bid now | Unrealised | Days to end |",
                  "|---|---|---:|---:|---:|---:|---:|"]
        rows = []
        for tok, p in positions.items():
            nm = names.get(tok, {})
            avg = p["cost"] / p["shares"] if p["shares"] else 0.0
            mark = marks.get(tok)
            unreal = (mark - avg) * p["shares"] if mark is not None else 0.0
            dte = (nm.get("end_ts", now) - now) / 86_400 if nm.get("end_ts") else float("nan")
            rows.append((dte, f"| {nm.get('question', tok[:12])[:70]} | {nm.get('outcome', '?')} | {p['shares']:.1f} | "
                              f"{avg:.3f} | {'%.3f' % mark if mark is not None else 'n/a'} | ${unreal:+.2f} | {dte:.0f} |"))
        lines += [r for _, r in sorted(rows, key=lambda x: x[0])]

    open_orders = [o for o in st.get("broker", {}).get("orders", {}).values() if o["status"] == "OPEN"]
    if open_orders:
        lines += ["", "## Resting orders", "", "| Market | Side | Price | Size | Filled |", "|---|---|---:|---:|---:|"]
        for o in open_orders:
            nm = names.get(o["token"], {})
            lines.append(f"| {nm.get('question', o['token'][:12])[:70]} | {o['side']} {nm.get('outcome', '')} | "
                         f"{o['price']:.3f} | {o['size']:.1f} | {o['filled']:.1f} |")

    if settlements:
        wins = sum(1 for s in settlements if float(s["pnl"]) > 0)
        total = sum(float(s["pnl"]) for s in settlements)
        lines += ["", "## Settled", "",
                  f"{len(settlements)} positions settled: {wins} won, {len(settlements) - wins} lost, "
                  f"net ${total:+.2f}.", "",
                  "| When | Market | Payoff | Profit |", "|---|---|---:|---:|"]
        for s in settlements[-15:]:
            lines.append(f"| {_when(float(s['ts']))} | {s['question'][:70]} | {s['payoff']} | ${float(s['pnl']):+.2f} |")

    if fills:
        lines += ["", "## Latest fills", "", "| When | Market | Side | Price | Size | Fee |", "|---|---|---|---:|---:|---:|"]
        for f in fills[-15:]:
            lines.append(f"| {_when(float(f['ts']))} | {f['question'][:60]} | {f['side']} | {float(f['price']):.3f} | "
                         f"{float(f['size']):.1f} | {float(f['fee']):.4f} |")

    if len(equity_rows) > 1:
        first, last = equity_rows[0], equity_rows[-1]
        times = [float(r["ts"]) for r in equity_rows]
        longest = max(b - a for a, b in zip(times, times[1:]))
        lines += ["", "## Equity history", "",
                  f"{len(equity_rows)} cycles from {_when(float(first['ts']))} to {_when(float(last['ts']))}; "
                  f"equity ${float(first['equity']):,.2f} → ${float(last['equity']):,.2f}. "
                  f"The longest gap between two cycles was {_span(longest)}."]
    return "\n".join(lines) + "\n"


def shadow_quiet(state_dir: str | Path, max_range: float = 0.03) -> dict[str, bool]:
    """For each forward-test signal with a recorded traded range: was it quiet when logged?

    Keyed "market:band", as in the log. A signal is quiet if it traded in the
    window, never more than ``max_range`` apart, in a market older than the
    window (the definition in trading/quiet.py and docs/04_second_round.md).
    """
    out: dict[str, bool] = {}
    for r in _read_csv(Path(state_dir) / "shadow_quiet.csv"):
        measured = r.get("range") not in (None, "")
        out[f"{r['market_id']}:{r.get('band', 'core')}"] = bool(
            int(r.get("complete", 0) or 0) and int(r.get("seasoned", 0) or 0) and measured
            and float(r["range"]) <= max_range + 1e-9)
    return out


def score_shadow(state_dir: str | Path, markets: dict[int, Any], band: str | None = None,
                 legs: bool | None = None, quiet: bool | None = None, side: str | None = None) -> dict[str, Any]:
    """Score the forward-test log against resolutions.

    ``markets`` maps market id to a ``LiveMarket``. Returns counts and the
    realised return per dollar of every resolved signal, bought at the logged
    ask plus fee. ``band`` keeps one price band; ``legs`` keeps only legs of
    multi-outcome events (True) or only stand-alone markets (False). The
    split uses facts logged with the signal, not the log's ``tradable``
    column, which records the configuration in force on the day and so goes
    stale when the rule is changed. ``quiet`` keeps the signals that were
    quiet when logged (True) or were not (False); signals whose traded range
    was never recorded belong to neither. ``side`` keeps the signals on the
    outcome named "No" (``"no"``) or "Yes" (``"yes"``).
    """
    rows = _read_csv(Path(state_dir) / "shadow.csv")
    if side is not None:
        rows = [r for r in rows if str(r.get("outcome_name", "")).strip().lower() == side]
    if band is not None:
        rows = [r for r in rows if r.get("band", "core") == band]
    if legs is not None:
        rows = [r for r in rows if bool(int(r.get("neg_risk", 0) or 0)) == legs]
    if quiet is not None:
        was_quiet = shadow_quiet(state_dir)
        rows = [r for r in rows if was_quiet.get(f"{r['market_id']}:{r.get('band', 'core')}") is quiet]
    resolved = []
    for r in rows:
        lm = markets.get(int(r["market_id"]))
        final0 = None if lm is None else lm.result0()
        if final0 is None:
            continue
        payoff = final0 if int(r["outcome"]) == 0 else 1.0 - final0
        cost = float(r["ask"]) + float(r["fee_ps"])
        resolved.append({"market_id": int(r["market_id"]), "event_id": int(r["event_id"]), "question": r["question"],
                         "cost": cost, "payoff": payoff, "ret": (payoff - cost) / cost, "p_model": float(r["p_model"])})
    n = len(resolved)
    out: dict[str, Any] = {"signals": len(rows), "resolved": n, "open": len(rows) - n, "rows": resolved}
    if n:
        rets = [x["ret"] for x in resolved]
        out["win_rate"] = sum(1 for x in resolved if x["payoff"] > x["cost"]) / n
        out["avg_ret"] = sum(rets) / n
        out["avg_cost"] = sum(x["cost"] for x in resolved) / n
        out["avg_p_model"] = sum(x["p_model"] for x in resolved) / n
        # event-clustered standard error: signals in one event are one bet
        by_event: dict[int, list[float]] = {}
        for x in resolved:
            by_event.setdefault(x["event_id"] if x["event_id"] >= 0 else -x["market_id"], []).append(x["ret"])
        g = len(by_event)
        mean = out["avg_ret"]
        if g > 1:
            ss = sum((sum(v) - mean * len(v)) ** 2 for v in by_event.values())
            out["se"] = (g / (g - 1) * ss) ** 0.5 / n
            out["t"] = mean / out["se"] if out["se"] > 0 else float("nan")
        out["events"] = g
    return out

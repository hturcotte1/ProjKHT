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
        lines += ["", "## Equity history", "",
                  f"{len(equity_rows)} cycles from {_when(float(first['ts']))} to {_when(float(last['ts']))}; "
                  f"equity ${float(first['equity']):,.2f} → ${float(last['equity']):,.2f}."]
    return "\n".join(lines) + "\n"


def score_shadow(state_dir: str | Path, markets: dict[int, Any], band: str | None = None) -> dict[str, Any]:
    """Score the forward-test log against resolutions.

    ``markets`` maps market id to a ``LiveMarket`` (closed ones carry
    ``final0``). Returns counts and the realised return per dollar of every
    resolved signal, bought at the logged ask plus fee.
    """
    rows = _read_csv(Path(state_dir) / "shadow.csv")
    if band is not None:
        rows = [r for r in rows if r.get("band", "core") == band]
    resolved = []
    for r in rows:
        lm = markets.get(int(r["market_id"]))
        if lm is None or not lm.closed or lm.final0 not in (0.0, 1.0, 0.5):
            continue
        payoff = lm.final0 if int(r["outcome"]) == 0 else 1.0 - lm.final0
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

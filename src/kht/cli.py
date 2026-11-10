"""Command line for the trading system.

    kht candidates   what the strategy would buy right now (no orders)
    kht cycle        run one trading cycle
    kht run          run cycles in a loop
    kht report       write the account status as Markdown
    kht geoblock     is this machine allowed to place orders?
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .api import Polymarket
from .trading.engine import build_engine
from .trading.report import build_report
from .trading.universe import scan_open

DEFAULT_CONFIG = "config/paper.json"
DEFAULT_STATE = "state/paper"


def _stamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())


def cmd_candidates(args: argparse.Namespace) -> int:
    pm = Polymarket()
    engine = build_engine(pm, args.state, args.config)
    markets = scan_open(pm, engine.strategy.cfg.min_volume)
    cands = engine.strategy.candidates(markets, time.time())
    print(f"{len(markets)} open markets scanned; {len(cands)} candidates")
    for c in cands[: args.top]:
        print(f"  {100 * c.daily_return * 365:6.0f}%/yr  {c.describe()}")
    return 0


def cmd_cycle(args: argparse.Namespace) -> int:
    engine = build_engine(Polymarket(), args.state, args.config)
    rep = engine.run_cycle()
    print(f"[{_stamp()}] equity ${rep.equity:,.2f}  cash ${rep.cash:,.2f}  positions {rep.n_positions}  "
          f"orders {rep.n_open_orders}  candidates {rep.n_candidates}  placed {rep.placed}  "
          f"blocked {rep.rejected}  fills {rep.new_fills}  settled {rep.settled}"
          f"{'  HALTED' if rep.halted else ''}")
    for note in rep.notes:
        print("   ", note)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(build_report(args.state))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    n = 0
    while args.cycles <= 0 or n < args.cycles:
        try:
            cmd_cycle(args)
        except Exception as exc:  # noqa: BLE001 - one bad cycle must not kill the loop
            print(f"[{_stamp()}] cycle failed: {exc!r}", file=sys.stderr, flush=True)
        n += 1
        sys.stdout.flush()
        if args.cycles <= 0 or n < args.cycles:
            time.sleep(args.interval)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    text = build_report(args.state)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text)
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


def cmd_geoblock(args: argparse.Namespace) -> int:
    info = Polymarket().geoblock()
    print(info)
    if info.get("blocked"):
        print("This machine's location may not place orders on Polymarket. Live trading must not run here.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="kht", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--config", default=DEFAULT_CONFIG)
        p.add_argument("--state", default=DEFAULT_STATE)

    p = sub.add_parser("candidates", help="show what would be bought now")
    common(p)
    p.add_argument("--top", type=int, default=25)
    p.set_defaults(fn=cmd_candidates)

    p = sub.add_parser("cycle", help="run one cycle")
    common(p)
    p.add_argument("--report", default=None, help="also write the Markdown status here")
    p.set_defaults(fn=cmd_cycle)

    p = sub.add_parser("run", help="run cycles in a loop")
    common(p)
    p.add_argument("--interval", type=float, default=900.0, help="seconds between cycles")
    p.add_argument("--cycles", type=int, default=0, help="stop after this many (0 = forever)")
    p.add_argument("--report", default=None)
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("report", help="write the account status")
    p.add_argument("--state", default=DEFAULT_STATE)
    p.add_argument("--out", default=None)
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("geoblock", help="check whether this machine may trade")
    p.set_defaults(fn=cmd_geoblock)

    args = ap.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())

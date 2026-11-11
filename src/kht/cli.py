"""Command line for the trading system.

    kht candidates   what the strategy would buy right now (no orders)
    kht cycle        run one trading cycle
    kht run          run cycles in a loop
    kht report       write the account status as Markdown
    kht shadow       score every signal ever seen against how it resolved
    kht us-record    write down the Polymarket US order books and their polymarket.com twins (read-only)
    kht us-rewards   paper orders before games on Polymarket US: what the reward formula would pay them (read-only)
    kht us-lasttick  crypto markets on Polymarket US in their last minutes: the books with sizes (read-only)
    kht us-quote     rest orders before games on Polymarket US: on paper unless live trading is switched on
    kht us-earnings  what the exchange says it paid in rewards, beside what the formula said (needs the account's key)
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


def cmd_shadow(args: argparse.Namespace) -> int:
    """Score every logged signal whose market has resolved."""
    import csv

    from .trading.report import score_shadow
    from .trading.universe import fetch_markets

    path = Path(args.state) / "shadow.csv"
    if not path.exists():
        print("no forward-test log yet")
        return 0
    with path.open() as fh:
        rows = list(csv.DictReader(fh))
    now = time.time()
    # only markets past their scheduled end can have resolved; saves requests
    due = sorted({int(r["market_id"]) for r in rows if float(r["end_ts"]) < now + 86_400 * args.lookahead_days})
    markets = fetch_markets(Polymarket(), due)
    # Only signals whose scheduled end has passed are scored. Counting early
    # resolutions as they happen would bias the result downward: a "by
    # December" market that closes in November is one where the thing happened.
    groups = [("core", False, None, None, "stand-alone markets in the traded band, either side"),
              # the third round's finding, checked on new data: the same prices on each side
              ("core", False, None, "no", "traded band, stand-alone, the NO side (what the accounts buy)"),
              ("core", False, None, "yes", "traded band, stand-alone, the YES side (logged only since the third round)"),
              ("core", True, None, None, "legs of multi-outcome events in the traded band (logged only)"),
              ("below", None, None, None, "below the traded band (logged only)"),
              # the third round's wider finding: the same mid prices on each side
              ("wide", False, None, "no", "mid prices up to the logged band, stand-alone, the NO side (logged only)"),
              ("wide", False, None, "yes", "mid prices up to the logged band, stand-alone, the YES side (logged only)"),
              ("above", None, None, None, "above the traded band (logged only)"),
              # the second round's finding, checked on new data: quiet against not quiet at the same prices
              ("core", False, True, None, "traded band, stand-alone, QUIET when logged (3c or less traded range over 7 days)"),
              ("core", False, False, None, "traded band, stand-alone, not quiet when logged"),
              ("below", False, True, None, "below the traded band, stand-alone, QUIET when logged"),
              ("below", False, False, None, "below the traded band, stand-alone, not quiet when logged")]
    for band, legs, quiet, side, label in groups:
        res = score_shadow(args.state, markets, band, legs, quiet, side)
        if not res["signals"]:
            continue
        print(f"\n{label}: {res['signals']} signals logged, {res['resolved']} resolved, {res['open']} still open")
        if res["resolved"]:
            print(f"  won {100 * res['win_rate']:.1f}% at an average cost of {100 * res['avg_cost']:.1f}c "
                  f"(model expected {100 * res['avg_p_model']:.1f}%)")
            line = f"  average return per signal: {100 * res['avg_ret']:+.2f}%"
            if "t" in res:
                line += f"   (t = {res['t']:.2f} across {res['events']} events)"
            print(line)
            for x in sorted(res["rows"], key=lambda r: r["ret"])[:3]:
                print(f"     worst: {100 * x['ret']:+7.1f}%  {x['question'][:80]}")
    return 0


def cmd_us_record(args: argparse.Namespace) -> int:
    """Write down the Polymarket US order books (and their polymarket.com twins). Reads public data only."""
    from .trading.us_recorder import record

    line = record(Path(args.state), with_twins=not args.no_twins, max_books=args.max_books)
    print(f"[{_stamp()}] Polymarket US recorder: {line['books_read']} books ({line['two_sided']} two-sided), {line['twins']} with a twin on "
          f"polymarket.com, {line['us_cheaper_yes'] + line['us_cheaper_no']} where the US price is cheaper by more than the fee; "
          f"{line['seconds']:.0f}s, {line['errors']} errors")
    return 0


def cmd_us_rewards(args: argparse.Namespace) -> int:
    """Follow games on Polymarket US before they start and score paper orders by the reward formula. Reads public data only."""
    from .trading.us_rewards import run

    line = run(Path(args.state), minutes=args.minutes, interval=args.interval)
    print(f"[{_stamp()}] Polymarket US paper orders: {line['minutes']:.0f} minutes, {line['games']} games followed ({line['games_quoted']} quoted), "
          f"{line['books']} books read, {line['hits']} times traded against, {line['errors']} errors")
    return 0


def cmd_us_lasttick(args: argparse.Namespace) -> int:
    """Record the books of crypto markets on Polymarket US in their last minutes. Reads public data only."""
    from .trading.us_lasttick import FOLLOW, run

    line = run(Path(args.state), minutes=args.minutes, budget=args.budget, follow=args.follow if args.follow else FOLLOW)
    print(f"[{_stamp()}] Polymarket US last minutes: {line['minutes']:.0f} minutes, {line['listings']} listings, {line['books']} readings of "
          f"{line['markets']} markets ending at {line['ends']} times, {line['errors']} errors")
    return 0


def cmd_us_quote(args: argparse.Namespace) -> int:
    """Rest orders before games on Polymarket US. On paper unless --live or --preview is given and the environment allows it."""
    from .api.http import Http
    from .api.polymarket_us import PolymarketUS
    from .trading.us_quoter import Engine, PaperBroker, QuoterConfig

    cfg = QuoterConfig.load(Path(args.config))
    state = Path(args.state)
    state.mkdir(parents=True, exist_ok=True)
    if args.live or args.preview:
        from .trading.us_live import LiveUSBroker

        broker, mode = LiveUSBroker.from_env(preview=args.preview), ("preview" if args.preview else "live")
    else:
        broker, mode = PaperBroker.load(state / "paper.json"), "paper"
    us = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": 6.0}))
    engine = Engine(state, cfg, broker, us, mode=mode)
    print(f"[{_stamp()}] Polymarket US orders before games: {mode}, {cfg.size:g} contracts a side, up to {cfg.max_games} games, "
          f"at most ${cfg.max_at_risk:,.0f} at risk")
    line = engine.run(args.minutes)
    print(f"[{_stamp()}] ended: {line}")
    print(f"[{_stamp()}] reward by the published formula so far: ${engine.reward():,.2f} (${engine.reward(1.0):,.2f} counting only a market and date at $1 or more)")
    return 0


def cmd_us_earnings(args: argparse.Namespace) -> int:
    """Set what the exchange credited beside what the formula said. This is the comparison the whole idea waits on."""
    import json

    from .trading.us_live import LiveUSBroker

    formula = json.loads((Path(args.state) / "accrued.json").read_text()) if (Path(args.state) / "accrued.json").exists() else {}
    paid = {(r.get("marketSlug"), r.get("date")): r for r in LiveUSBroker.from_env(preview=True).earnings(args.since)}
    keys = sorted(set(paid) | {(s, d) for s, by in formula.items() for d in by if args.since is None or d >= args.since}, key=lambda k: (k[1], k[0]))
    print(f"{'date':10}  {'market':56}  {'formula':>8}  {'credited':>8}  status")
    total_f = total_p = 0.0
    for slug, date in keys:
        f, r = formula.get(slug, {}).get(date, 0.0), paid.get((slug, date), {})
        total_f, total_p = total_f + f, total_p + float(r.get("reward") or 0.0)
        print(f"{date:10}  {slug[:56]:56}  {f:8.2f}  {float(r.get('reward') or 0.0):8.2f}  {r.get('status', '-')}")
    print(f"{'':10}  {'total':56}  {total_f:8.2f}  {total_p:8.2f}")
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

    p = sub.add_parser("shadow", help="score the forward-test log of all signals")
    p.add_argument("--state", default=DEFAULT_STATE)
    p.add_argument("--lookahead-days", type=float, default=0.0,
                   help="also check markets ending within this many days (they may resolve early)")
    p.set_defaults(fn=cmd_shadow)

    p = sub.add_parser("us-record", help="record Polymarket US order books and their polymarket.com twins (read-only)")
    p.add_argument("--state", default="state/us")
    p.add_argument("--no-twins", action="store_true", help="skip polymarket.com")
    p.add_argument("--max-books", type=int, default=None, help="read at most this many books (for a quick trial)")
    p.set_defaults(fn=cmd_us_record)

    p = sub.add_parser("us-rewards", help="paper orders before games on Polymarket US, scored by the reward formula (read-only)")
    p.add_argument("--state", default="state/us-rewards")
    p.add_argument("--minutes", type=float, default=300.0, help="how long to follow the order books")
    p.add_argument("--interval", type=float, default=120.0, help="seconds between readings of one book")
    p.set_defaults(fn=cmd_us_rewards)

    p = sub.add_parser("us-lasttick", help="record crypto markets on Polymarket US in their last minutes, with sizes (read-only)")
    p.add_argument("--state", default="state/us-lasttick")
    p.add_argument("--minutes", type=float, default=300.0, help="how long to record")
    p.add_argument("--budget", type=float, default=5.0, help="requests a second, at most")
    p.add_argument("--follow", type=float, default=None, help="seconds before a market's end at which its book is first read (for trials only)")
    p.set_defaults(fn=cmd_us_lasttick)

    p = sub.add_parser("us-quote", help="rest orders before games on Polymarket US (on paper unless switched on)")
    p.add_argument("--config", default="config/us_quoter.json")
    p.add_argument("--state", default="state/us-quoter")
    p.add_argument("--minutes", type=float, default=60.0, help="how long to run; the orders are pulled when it ends")
    p.add_argument("--live", action="store_true", help="send real orders (also needs the environment switch and the account's key)")
    p.add_argument("--preview", action="store_true", help="read the real account and send every order to the exchange's preview only")
    p.set_defaults(fn=cmd_us_quote)

    p = sub.add_parser("us-earnings", help="rewards the exchange credited, beside what the formula said")
    p.add_argument("--state", default="state/us-quoter")
    p.add_argument("--since", default=None, help="first date, YYYY-MM-DD")
    p.set_defaults(fn=cmd_us_earnings)

    p = sub.add_parser("geoblock", help="check whether this machine may trade")
    p.set_defaults(fn=cmd_geoblock)

    args = ap.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())

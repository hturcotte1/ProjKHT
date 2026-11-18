"""Test R2 on what ``kht us-rewards`` records from 19 November 2026: resting orders before UTR matches.

docs/13_round_six.md, section 3. A paper account: no order was placed and no
reward was paid to anyone.

    python scripts/us_rewards2_score.py --settle

Two accounts are judged, each named before any of its games had been
recorded:

    R2-utr   the rule of test R1 unchanged (docs/09, section 5), UTR only, 250 contracts a side
    R2-top   the same games, the orders at the best price itself, 100 contracts a side

Both are read from the same order-book readings. The first is written to
state/us-rewards, the second to state/us-rewards-top. Only games whose
start is on or after 19 November 2026 (US Eastern) count: the week before
it is where the idea came from. Everything else recorded is described.

It uses the accounting of scripts/us_rewards_score.py and changes none of it.
Writes reports/research/usr2_*.csv and usr2_summary.txt.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

_spec = importlib.util.spec_from_file_location("us_rewards_score", Path(__file__).resolve().parent / "us_rewards_score.py")
usr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(usr)

OUT = ROOT / "reports" / "research"
COUNTED_FROM = 1_795_064_400.0      # 19 November 2026, 00:00 US Eastern (05:00 UTC): games starting from here count
PROGRAMME = "utr_moneyline"
ACCOUNTS = (("R2-utr", "us-rewards", 250, "the rule of R1, 250 contracts a side"),
            ("R2-top", "us-rewards-top", 100, "orders at the best price itself, 100 contracts a side"))
MIN_GAMES, MIN_DATES, BAR = 800, 12, 3.0
SIZES = (25, 50, 100, 250, 500)
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)


def counted(g: pd.DataFrame, h: pd.DataFrame, since: float = COUNTED_FROM) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The games that count for R2, and the fills in them: every game whose start, as last recorded, is on or after ``since``."""
    if not len(g):
        return g, h
    start = g.groupby("slug")["start"].max()
    keep = set(start.index[start >= since])
    return g[g["slug"].isin(keep)], (h[h["slug"].isin(keep)] if len(h) else h)


def judged(per: pd.DataFrame, programme: str = PROGRAMME) -> pd.DataFrame:
    """The games of one account that the judge takes: the programme's own-pool games, old enough and settled."""
    return per[(per["markets_in_event"] == 1) & per["program"].str.startswith(programme) & per["over"] & per["settle"].notna()]


def verdict(j: pd.DataFrame) -> tuple[str, float, float, int]:
    """The bar of docs/13, section 3: at least 800 games on at least 12 US dates; mean net a game above zero with z of 3, each date one observation."""
    n, dates = len(j), j["day"].nunique() if len(j) else 0
    if not n:
        return "NOT YET JUDGED: no game has settled", float("nan"), float("nan"), 0
    mean, z, k = usr.clustered_z(j["net"].to_numpy(), j["day"].to_numpy())
    if n < MIN_GAMES or dates < MIN_DATES:
        return f"NOT YET JUDGED: {n:,} games on {dates} US dates; {MIN_GAMES:,} on {MIN_DATES} are asked for", mean, z, k
    return ("PASSES" if mean > 0 and z >= BAR else "DOES NOT PASS") + f": {n:,} games on {dates} US dates, ${mean:,.3f} a game, z {z:.2f} (at least {BAR:g} asked)", mean, z, k


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=str(ROOT / "state"), help="the folder that holds us-rewards and us-rewards-top")
    ap.add_argument("--settle", action="store_true", help="look up how finished games settled (public data)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    base, out = Path(args.state), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    now = time.time()
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say("Test R2: resting orders before UTR matches (docs/13_round_six.md, section 3)")
    say(f"scored {pd.Timestamp.now(tz='UTC'):%d %B %Y, %H:%M} UTC. Paper accounts. No order was placed and no reward was paid to anyone.")
    say(f"games count from {pd.Timestamp(COUNTED_FROM, unit='s', tz='UTC').tz_convert('America/New_York'):%d %B %Y} (US Eastern)")
    for name, folder, size, what in ACCOUNTS:
        state = base / folder
        g, h, log = usr.load(state) if (state / "runs").exists() else (pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        g, h = counted(g, h)
        say()
        say(f"===== {name}: {what} =====")
        if not len(g):
            say("nothing recorded yet")
            continue
        d, facts = usr.per_game_day(g), usr.game_facts(g)
        finished = sorted(facts.index[facts["start"] < now - 12 * 3600])
        settle = usr.settlements(base / "us-rewards", finished, args.settle)        # one file of settlements serves both accounts
        say(f"games followed since then: {d['slug'].nunique():,}; started more than 12 hours ago: {len(finished):,}; of them settled: "
            f"{int(pd.Index(finished).isin(settle.index).sum()):,}")
        per, f = usr.account(d, facts, h, settle, size, now)
        j = judged(per)
        text, mean, z, k = verdict(j)
        if len(j):
            say(f"UTR, {size} contracts a side: reward by the formula ${j['reward_formula'].sum():,.2f}; after the $1 minimum ${j['reward_paid'].sum():,.2f}; "
                f"games traded against {int((j['filled'] > 1e-9).sum()):,} of {len(j):,} ({j['filled'].sum():,.0f} contracts)")
            say(f"   fills held to the result ${j['pnl_settle'].sum():,.2f}; at the last middle before the start ${j['pnl_mid'].sum():,.2f}; "
                f"net ${j['net'].sum():,.2f}; a game ${mean:,.3f}; z by date {z:.2f} over {k} dates")
            say("   if rewards were capped at a share of the account's own executed volume (described only): "
                + "; ".join(f"{pct}%: ${j[f'reward_cap_{pct}'].sum():,.2f}" for pct in usr.CAPS))
            by_day = usr.table_by(j, "day")
            by_day.round(3).to_csv(out / f"usr2_by_day_{name.lower().replace('-', '_')}.csv", index=False)
            say(by_day[["day", "games", "hours_quoted", "share_of_score", "reward_paid", "games_filled", "contracts_filled", "fills_at_settlement", "fills_at_last_mid",
                        "net", "net_a_game"]].round(3).to_string(index=False))
        say(f"Verdict by the bar fixed in advance, {name}: {text}")
        # described: every size on UTR, and every programme at the judged size
        rows = []
        for x in SIZES:
            p, _ = usr.account(d, facts, h, settle, x, now)
            q = judged(p)
            if len(q):
                m, zz, kk = usr.clustered_z(q["net"].to_numpy(), q["day"].to_numpy())
                rows.append({"contracts_a_side": x, "games": len(q), "reward_paid": q["reward_paid"].sum(), "contracts_filled": q["filled"].sum(),
                             "fills_at_settlement": q["pnl_settle"].sum(), "fills_at_last_mid": q["pnl_mid"].sum(), "net": q["net"].sum(), "net_a_game": m, "z_by_date": zz})
        if rows:
            t = pd.DataFrame(rows)
            t.round(3).to_csv(out / f"usr2_by_size_{name.lower().replace('-', '_')}.csv", index=False)
            say("   UTR at every order size (described; only the size named above is judged)")
            say(t.round(3).to_string(index=False))
        own = per[(per["markets_in_event"] == 1) & per["over"] & per["settle"].notna()]
        if len(own):
            t = usr.table_by(own, "program").sort_values("games", ascending=False)
            t.round(3).to_csv(out / f"usr2_by_programme_{name.lower().replace('-', '_')}.csv", index=False)
            say(f"   every programme at {size} contracts a side (described)")
            say(t[["program", "games", "share_of_score", "reward_paid", "games_filled", "contracts_filled", "fills_at_settlement", "fills_at_last_mid", "net",
                   "net_a_game"]].round(3).to_string(index=False))
    (out / "usr2_summary.txt").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

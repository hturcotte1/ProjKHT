"""Is a trading cycle due?

GitHub starts scheduled jobs late and drops some of them, more so in a new
repository. A workflow scheduled every three hours can therefore go many hours
without running. So the workflow is scheduled far more often than the accounts
need to trade, and every run first asks this module whether enough time has
passed since the last cycle *started*. A dropped slot then costs minutes, not
hours, and the accounts still trade at the pace that was intended.

The time of the last start is kept in a one-line text file (the "stamp"). It
records attempts, not successes, so a cycle that keeps failing is retried at
the normal pace instead of on every slot.

Run as a module so that it works before anything is installed:

    PYTHONPATH=src python3 -m kht.trading.schedule state/last_cycle_started --min-minutes 170 --mark

Exit code 0 means a cycle is due, 3 means it is not. Anything else is an error
and should stop the run: guessing either way would be wrong.

Only the standard library is used.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

NOT_DUE = 3
_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def read_stamp(path: Path) -> datetime | None:
    """The time in the stamp file, or None if there is no usable one."""
    try:
        text = path.read_text().strip()
    except (OSError, UnicodeDecodeError):
        return None
    if not text:
        return None
    try:
        when = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when


def _ago(minutes: float) -> str:
    if minutes < 1:
        return "less than a minute ago"
    if minutes < 180:
        return f"{minutes:.0f} minutes ago"
    if minutes < 72 * 60:
        return f"{minutes / 60:.1f} hours ago"
    return f"{minutes / 1440:,.0f} days ago"


def check(stamp: Path, min_minutes: float, now: datetime) -> tuple[bool, str]:
    """Whether a cycle is due, and a sentence saying why.

    A missing, unreadable or future-dated stamp counts as due: the worst that
    does is one early cycle, after which the stamp is good again.
    """
    last = read_stamp(stamp)
    if last is None:
        return True, "due: no record of an earlier cycle"
    age = (now - last).total_seconds() / 60.0
    if age < 0:
        return True, "due: the last cycle is recorded in the future, so the record is ignored"
    if age >= min_minutes:
        return True, f"due: the last cycle started {_ago(age)}"
    after = last + timedelta(minutes=min_minutes)
    return False, (
        f"not due: the last cycle started {_ago(age)}; "
        f"the next is due after {after:%H:%M} UTC"
    )


def mark(stamp: Path, now: datetime) -> None:
    """Record `now` as the start of a cycle."""
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(now.astimezone(timezone.utc).strftime(_FORMAT) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m kht.trading.schedule",
        description="Exit 0 if a trading cycle is due, 3 if it is not.",
    )
    ap.add_argument("stamp", type=Path, help="file holding the time the last cycle started")
    ap.add_argument(
        "--min-minutes", type=float, default=0.0,
        help="minutes that must have passed since the last start (default 0: always due)",
    )
    ap.add_argument("--mark", action="store_true", help="if a cycle is due, record now as its start")
    args = ap.parse_args(argv)

    now = datetime.now(timezone.utc)
    due, why = check(args.stamp, args.min_minutes, now)
    if due and args.mark:
        mark(args.stamp, now)
    print(why)
    return 0 if due else NOT_DUE


if __name__ == "__main__":
    sys.exit(main())

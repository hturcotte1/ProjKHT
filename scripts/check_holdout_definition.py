"""Do the pre-registered verdicts depend on how the holdout was defined?

The pre-registration (docs/01_thinking_session.md, section 8) describes the
holdout as "markets that closed before 2026-06-08". The confirmatory script,
committed before the holdout was opened, splits on the *scheduled* end date
instead (before 2026-05-01), because a split on the realised close date
conditions on the outcome: a "by December" market that closes in May is one
where the event happened. This script reports every pre-registered rule under
both definitions, and counts trades that sit in the holdout as run but in a
market that had already been examined (closed on or after 2026-06-08).

It reads the saved trade lists, so it needs the market metadata but not the
trade tapes.

Usage: python scripts/check_holdout_definition.py [--out reports/research]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from kht.data.download import load_meta
from kht.research.stats import mean_cluster

SPLIT_TS = pd.Timestamp("2026-05-01", tz="UTC").timestamp()
SEEN_TS = pd.Timestamp("2026-06-08", tz="UTC").timestamp()
RULES = ("R1", "R1a", "R1b", "R1c", "R1d", "R2", "R3", "R1m", "longshot", "mid")


def summary(g: pd.DataFrame) -> dict:
    if len(g) < 20:
        return {"trades": len(g)}
    r = mean_cluster(g["ret"].to_numpy(), g["cluster"].to_numpy())
    return {"trades": len(g), "events": int(g["cluster"].nunique()),
            "won %": 100 * float((g["proceeds"] > g["cost"]).mean()), "ret %": 100 * r.mean, "t": r.t}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/research")
    args = ap.parse_args()
    out = Path(args.out)
    meta = load_meta("closed").set_index("market_id")
    rows = []
    for rule in RULES:
        path = out / f"c2_trades_{rule}.csv"
        if not path.exists():
            continue
        t = pd.read_csv(path)
        closed = meta["closed_ts"].reindex(t["market_id"]).to_numpy()
        by_schedule = meta["end_ts"].reindex(t["market_id"]).to_numpy() < SPLIT_TS
        unseen = closed < SEEN_TS
        for name, mask in (("as run: scheduled end before 2026-05-01", by_schedule),
                           ("as written: closed before 2026-06-08", unseen),
                           ("both conditions", by_schedule & unseen)):
            rows.append({"rule": rule, "holdout": name, **summary(t[mask])})
        rows.append({"rule": rule, "holdout": "in the holdout as run, but already examined", "trades": int((by_schedule & ~unseen).sum())})
    res = pd.DataFrame(rows)
    res.to_csv(out / "c5_holdout_definitions.csv", index=False)
    pd.set_option("display.width", 200)
    print(res.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

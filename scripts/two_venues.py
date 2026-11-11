"""Two exchanges, one question: Polymarket US against polymarket.com (docs/07_two_venues.md).

    python scripts/two_venues.py pairs      # the polymarket.com twin of every settled US market -> data/two/pairs.parquet
    python scripts/two_venues.py prices     # hourly polymarket.com prices of the twins -> data/two/prices/*.parquet
    python scripts/two_venues.py table      # one row per US market-day with both prices -> data/cache/two_venues.parquet
    python scripts/two_venues.py test       # the tests fixed in docs/07, section 3 -> reports/research/tv_*

Pairing is the strict rule of ``kht.trading.twins``: same event title, same
answer label. Everything here reads public data; nothing is traded.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.api.polymarket import GAMMA, Polymarket
from kht.api.polymarket_us import taker_fee_per_share
from kht.trading.twins import norm, pair_event

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
pd.set_option("display.max_colwidth", 80)
ROOT = Path(__file__).resolve().parents[1]
US = ROOT / "data" / "us"
TWO = ROOT / "data" / "two"
OUT = ROOT / "reports" / "research"
CACHE = ROOT / "data" / "cache"
HOUR = 3600


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def us_meta() -> tuple[pd.DataFrame, pd.DataFrame]:
    m = pd.concat([pd.read_parquet(p) for p in sorted(US.glob("markets*.parquet"))], ignore_index=True).drop_duplicates("market_id")
    e = pd.concat([pd.read_parquet(p) for p in sorted(US.glob("events*.parquet"))], ignore_index=True).drop_duplicates("event_id")
    return m, e


# ------------------------------------------------------------------ pairs
def cmd_pairs(args: argparse.Namespace) -> None:
    """Search polymarket.com for an event with the same title as each settled US event, and pair their markets."""
    TWO.mkdir(parents=True, exist_ok=True)
    m, e = us_meta()
    m = m[m["yes_settle"].notna() & m["event_id"].notna()]
    titles = e.set_index("event_id")["event_title"]
    groups = [(eid, titles.get(eid), g) for eid, g in m.groupby("event_id")]
    groups = [(eid, t, g) for eid, t, g in groups if isinstance(t, str) and t.strip()]
    raw_path = TWO / "intl_events.jsonl"
    done: dict[str, list[dict]] = {}
    if raw_path.exists():
        for line in raw_path.open():
            d = json.loads(line)
            done[d["q"]] = d["events"]
    todo = sorted({t for _, t, _ in groups} - set(done))
    log(f"{len(groups):,} settled US events, {len({t for _, t, _ in groups}):,} distinct titles, {len(todo):,} to look up")
    pm = Polymarket()

    def find(title: str) -> tuple[str, list[dict] | None]:
        try:
            d = pm.http.get(GAMMA + "/public-search", {"q": title, "limit_per_type": 20})
        except Exception:
            return title, None
        key = norm(title)
        keep = []
        for ev in d.get("events") or []:
            if norm(ev.get("title")) != key:
                continue
            keep.append({"id": ev.get("id"), "title": ev.get("title"), "endDate": ev.get("endDate"), "closed": ev.get("closed"), "negRisk": ev.get("negRisk"),
                         "volume": ev.get("volume"),
                         "markets": [{k: mk.get(k) for k in ("id", "question", "groupItemTitle", "outcomes", "outcomePrices", "clobTokenIds", "conditionId", "closed",
                                                             "closedTime", "endDate", "startDate", "volume", "negRisk", "umaResolutionStatus")}
                                     for mk in ev.get("markets") or []]})
        return title, keep

    t0, n = time.time(), 0
    with raw_path.open("a") as fh, cf.ThreadPoolExecutor(max_workers=4) as pool:
        for title, evs in pool.map(find, todo):
            n += 1
            if evs is not None:
                done[title] = evs
                fh.write(json.dumps({"q": title, "events": evs}) + "\n")
            if n % 500 == 0:
                log(f"   {n:,}/{len(todo):,} ({n / (time.time() - t0):.1f}/s)")
    rows = []
    for eid, title, g in groups:
        cands = done.get(title) or []
        us_event = {"title": title, "endDate": pd.to_datetime(g["end_ts"].max(), unit="s", utc=True).isoformat(),
                    "markets": [{"slug": r.slug, "title": r.title} for r in g.itertuples()]}
        by_id = {str(mk.get("id")): (mk, ev) for ev in cands for mk in ev.get("markets") or []}
        for tw in pair_event(us_event, cands):
            mk, ev = by_id[tw.intl_id]
            try:
                paid = float(json.loads(mk.get("outcomePrices") or "[]")[0])
            except (ValueError, IndexError, TypeError):
                paid = float("nan")
            rows.append({"slug": tw.us_slug, "event_id": eid, "intl_id": tw.intl_id, "token_yes": tw.token_yes, "condition": tw.condition, "rule": tw.rule,
                         "intl_event_id": tw.intl_event_id, "intl_label": tw.intl_label, "intl_question": tw.intl_question, "neg_risk": tw.neg_risk,
                         "intl_closed": bool(mk.get("closed")), "intl_yes_paid": paid, "intl_volume": float(mk.get("volume") or "nan"),
                         "intl_closed_ts": pd.Timestamp(mk["closedTime"]).timestamp() if mk.get("closedTime") else float("nan"),
                         "intl_start_ts": pd.Timestamp(mk["startDate"]).timestamp() if mk.get("startDate") else float("nan")})
    pairs = pd.DataFrame(rows).drop_duplicates("slug")
    dup = pairs["intl_id"].duplicated(keep=False)           # a polymarket.com market claimed by two US markets pairs with neither
    pairs = pairs[~dup].merge(m[["slug", "market_id", "category", "question", "title", "yes_settle", "end_ts"]], on="slug")
    pairs.to_parquet(TWO / "pairs.parquet", index=False)
    with_title = sum(1 for _, t, _ in groups if done.get(t))
    log(f"US events with a same-titled event on polymarket.com: {with_title:,} of {len(groups):,}; markets paired: {len(pairs):,} "
        f"({int(dup.sum())} dropped as claimed twice) in {pairs['event_id'].nunique():,} events")
    print(pairs.groupby(["category", "rule"]).size().unstack(fill_value=0).to_string())
    # do the two contracts pay the same side? (a check on the pairing, not a test of anything)
    both = pairs[pairs["intl_closed"] & pairs["intl_yes_paid"].isin([0.0, 1.0]) & pairs["yes_settle"].isin([0.0, 1.0])]
    agree = both["intl_yes_paid"] == both["yes_settle"]
    log(f"both settled at 0 or 1: {len(both):,}; same side paid: {int(agree.sum()):,} ({100 * agree.mean():.2f}%); "
        f"US settled between 0 and 1: {int((~pairs['yes_settle'].isin([0.0, 1.0])).sum())}; twin not yet closed: {int((~pairs['intl_closed']).sum())}")
    bad = both[~agree]
    if len(bad):
        print("pairs that paid different sides:")
        print(bad[["category", "question", "title", "intl_question", "yes_settle", "intl_yes_paid"]].head(40).to_string(index=False))


# ------------------------------------------------------------------ prices
def cmd_prices(args: argparse.Namespace) -> None:
    """Hourly polymarket.com price of each twin's "Yes" token over its whole life."""
    pairs = pd.read_parquet(TWO / "pairs.parquet")
    dest = TWO / "prices"
    dest.mkdir(parents=True, exist_ok=True)
    have: set[str] = set()
    for p in dest.glob("*.parquet"):
        have |= set(pd.read_parquet(p, columns=["intl_id"])["intl_id"].unique())
    marks = dest / "empty.txt"
    if marks.exists():
        have |= set(marks.read_text().split())
    todo = pairs[~pairs["intl_id"].isin(have)]
    log(f"{len(pairs):,} twins, {len(todo):,} price series to fetch")
    pm = Polymarket()

    def one(row) -> tuple[str, list[tuple[int, float]] | None]:
        try:
            return row.intl_id, pm.prices_history(row.token_yes, interval="max", bucket_seconds=args.bucket)
        except Exception:
            return row.intl_id, None

    buf, empty, part, n, t0 = [], [], 0, 0, time.time()

    def flush() -> None:
        nonlocal buf, empty, part
        if buf:
            pd.DataFrame(buf, columns=["intl_id", "ts", "price"]).to_parquet(dest / f"p_{int(time.time())}_{part}.parquet", index=False)
            part += 1
            buf = []
        if empty:
            with marks.open("a") as fh:
                fh.write("\n".join(empty) + "\n")
            empty = []

    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        for iid, pts in pool.map(one, list(todo.itertuples())):
            n += 1
            if pts is None:
                continue
            if pts:
                buf.extend((iid, t, p) for t, p in pts)
            else:
                empty.append(iid)
            if len(buf) >= 500_000:
                flush()
            if n % 500 == 0:
                log(f"   {n:,}/{len(todo):,} ({n / (time.time() - t0):.1f}/s)")
    flush()
    log(f"prices: finished {n:,} in {time.time() - t0:.0f}s")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pairs").set_defaults(fn=cmd_pairs)
    p = sub.add_parser("prices")
    p.add_argument("--bucket", type=int, default=HOUR)
    p.set_defaults(fn=cmd_prices)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

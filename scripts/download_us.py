"""Download Polymarket US market lists, settlements and price history (public gateway, no key).

    python scripts/download_us.py meta                 # every market and event -> data/us/markets.parquet, events.parquet
    python scripts/download_us.py history [--shard i/n] [--only closed|open|all] [--categories politics,culture]
    python scripts/download_us.py volume  [--categories ...]   # shares traded and open interest, one request a market

History is the daily series the gateway keeps for a market's whole life: the
ask of "Yes" and the ask of "No" as read from the order book at midnight UTC.
It lands in data/us/history/<shard>.parquet, one row per market per day.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import time
from pathlib import Path

import pandas as pd

from kht.api.polymarket_us import PolymarketUS, yes_settlement
from kht.data.download import log

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "us"
# Crypto is left out by default: over 400,000 settled markets, nearly all hourly and shorter price ladders.
CATEGORIES = ("politics", "culture", "macro", "technology", "climate", "finance", "geopolitics", "science", "sports")


def ts(value: str | None) -> float:
    if not value:
        return float("nan")
    try:
        return pd.Timestamp(value).timestamp()
    except (ValueError, TypeError):
        return float("nan")


def market_row(m: dict) -> dict:
    tags = m.get("tags") or []
    terms = m.get("assetPriceTerms") or {}
    return {
        "market_id": int(m["id"]), "slug": m.get("slug"), "question": m.get("question"), "title": m.get("title"),
        "subtitle": m.get("subtitle"), "category": m.get("category"), "subcategory": m.get("eventSubcategory"),
        "market_type": m.get("marketType"), "sports_type": m.get("sportsMarketType"), "line": m.get("line"),
        "start_ts": ts(m.get("startDate")), "end_ts": ts(m.get("endDate")), "created_ts": ts(m.get("createdAt")),
        "updated_ts": ts(m.get("updatedAt")), "game_start_ts": ts(m.get("gameStartTime")),
        "status": m.get("status"), "closed": bool(m.get("closed")), "active": bool(m.get("active")),
        "yes_settle": yes_settlement(m), "tick": m.get("orderPriceMinTickSize"), "min_qty": m.get("minimumTradeQty"),
        "fee_theta": m.get("feeCoefficient"), "combo": bool(m.get("comboEnabled")),
        "tags": "|".join(str(t.get("slug") or t.get("label") or t.get("id")) for t in tags if isinstance(t, dict)),
        "asset": terms.get("asset"), "asset_market_type": terms.get("marketType"),
        "best_bid": float((m.get("bestBidQuote") or {}).get("value") or "nan"),
        "best_ask": float((m.get("bestAskQuote") or {}).get("value") or "nan"),
    }


def cmd_meta(args: argparse.Namespace) -> None:
    pm = PolymarketUS()
    OUT.mkdir(parents=True, exist_ok=True)
    rows: dict[int, dict] = {}
    cats = args.categories.split(",") if args.categories else CATEGORIES
    # Listed in order of id so that markets created while the listing runs land at the end, not in the middle.
    for cat in cats:
        n = 0
        for m in pm.iter_markets(closed=True, categories=cat, orderBy="id", orderDirection="asc"):
            rows[int(m["id"])] = market_row(m)
            n += 1
            if n % 20000 == 0:
                log(f"   closed, {cat}: {n} ...")
        log(f"closed, {cat}: {n}")
    n = 0
    for m in pm.iter_markets(closed=False, orderBy="id", orderDirection="asc"):
        if m.get("category") in cats:
            rows[int(m["id"])] = market_row(m)
            n += 1
    log(f"open: {n}")
    markets = pd.DataFrame(list(rows.values()))
    # events say which markets belong together (one race, one game, one question with several answers)
    ev_rows, link = [], []
    for closed in (True, False):
        for e in pm.iter_events(closed=closed, orderBy="id", orderDirection="asc"):
            ev_rows.append({"event_id": int(e["id"]), "event_slug": e.get("slug"), "event_title": e.get("title"), "event_category": e.get("category"),
                            "series": e.get("seriesSlug"), "event_start_ts": ts(e.get("startDate")), "event_end_ts": ts(e.get("endDate")),
                            "event_closed": bool(e.get("closed")), "n_markets": len(e.get("markets") or []),
                            "event_tags": "|".join(str(t.get("slug") or t.get("label")) for t in (e.get("tags") or []) if isinstance(t, dict))})
            for m in e.get("markets") or []:
                link.append((int(m["id"]), int(e["id"])))
        log(f"events, closed={closed}: {len(ev_rows)} so far")
    events = pd.DataFrame(ev_rows).drop_duplicates("event_id")
    links = pd.DataFrame(link, columns=["market_id", "event_id"]).drop_duplicates("market_id")
    markets = markets.merge(links, on="market_id", how="left")
    markets.to_parquet(OUT / "markets.parquet", index=False)
    events.to_parquet(OUT / "events.parquet", index=False)
    log(f"{len(markets):,} markets ({int(markets['closed'].sum()):,} closed, {int(markets['yes_settle'].notna().sum()):,} settled), "
        f"{len(events):,} events; {int(markets['event_id'].isna().sum()):,} markets without an event")
    print(markets.groupby(["category", "closed"]).size().unstack(fill_value=0).to_string())


def pick(args: argparse.Namespace) -> pd.DataFrame:
    m = pd.read_parquet(OUT / "markets.parquet")
    if args.only == "closed":
        m = m[m["closed"]]
    elif args.only == "open":
        m = m[~m["closed"]]
    if args.categories:
        m = m[m["category"].isin(args.categories.split(","))]
    m = m.sort_values("market_id")
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        m = m.iloc[i::n]
    return m


def cmd_history(args: argparse.Namespace) -> None:
    pm = PolymarketUS()
    m = pick(args)
    dest = OUT / "history"
    dest.mkdir(parents=True, exist_ok=True)
    tag = (args.shard or "0/1").replace("/", "of") + ("_" + args.only) + ("_" + args.categories.replace(",", "-") if args.categories else "")
    done: set[str] = set()
    for p in dest.glob("*.parquet"):
        done |= set(pd.read_parquet(p, columns=["slug"])["slug"].unique())
    marks = dest / "empty.txt"                     # markets the gateway has no observations for
    if marks.exists():
        done |= set(marks.read_text().split())
    todo = [s for s in m["slug"] if s not in done]
    log(f"history: {len(m):,} markets, {len(todo):,} to fetch")

    def one(slug: str) -> tuple[str, list[tuple[int, float, float]] | None]:
        try:
            return slug, pm.price_history(slug)
        except Exception:                           # keep going; a market that failed is retried on the next run
            return slug, None

    buf: list[tuple[str, int, float, float]] = []
    empty: list[str] = []
    part, t0, n = 0, time.time(), 0

    def flush() -> None:
        nonlocal buf, part, empty
        if buf:
            pd.DataFrame(buf, columns=["slug", "ts", "yes_ask", "no_ask"]).to_parquet(dest / f"{tag}_{int(time.time())}_{part}.parquet", index=False)
            part += 1
            buf = []
        if empty:
            with marks.open("a") as fh:
                fh.write("\n".join(empty) + "\n")
            empty = []

    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for slug, pts in pool.map(one, todo):
            n += 1
            if pts is None:
                continue
            if pts:
                buf.extend((slug, t, a, b) for t, a, b in pts)
            else:
                empty.append(slug)
            if len(buf) >= 400_000:
                flush()
            if n % 2000 == 0:
                rate = n / (time.time() - t0)
                log(f"history: {n:,}/{len(todo):,} ({rate:.1f}/s, eta {(len(todo) - n) / rate / 60:.0f} min)")
    flush()
    log(f"history: finished {n:,} markets in {time.time() - t0:.0f}s")


def cmd_volume(args: argparse.Namespace) -> None:
    pm = PolymarketUS()
    m = pick(args)
    path = OUT / "volume.parquet"
    have = pd.read_parquet(path) if path.exists() else pd.DataFrame(columns=["slug", "shares_traded", "open_interest", "settle_px", "last_px", "asof"])
    todo = [s for s in m["slug"] if s not in set(have["slug"])]
    log(f"volume: {len(m):,} markets, {len(todo):,} to fetch")

    def one(slug: str) -> dict | None:
        try:
            b = pm.bbo(slug)
        except Exception:
            return None
        f = lambda key: float((b.get(key) or {}).get("value")) if isinstance(b.get(key), dict) and (b.get(key) or {}).get("value") not in (None, "") else float("nan")  # noqa: E731
        return {"slug": slug, "shares_traded": float(b.get("sharesTraded") or "nan"), "open_interest": float(b.get("openInterest") or "nan"),
                "settle_px": f("settlementPx"), "last_px": f("lastTradePx"), "asof": time.time()}

    rows, t0 = [], time.time()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, r in enumerate(pool.map(one, todo), 1):
            if r:
                rows.append(r)
            if i % 5000 == 0:
                log(f"volume: {i:,}/{len(todo):,} ({i / (time.time() - t0):.1f}/s)")
                pd.concat([have, pd.DataFrame(rows)], ignore_index=True).to_parquet(path, index=False)
    pd.concat([have, pd.DataFrame(rows)], ignore_index=True).to_parquet(path, index=False)
    log(f"volume: {len(rows):,} fetched")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("meta")
    p.add_argument("--categories", default=None, help="comma-separated; default is everything except crypto")
    p.set_defaults(fn=cmd_meta)
    for name, fn in (("history", cmd_history), ("volume", cmd_volume)):
        p = sub.add_parser(name)
        p.add_argument("--shard", default=None)
        p.add_argument("--only", default="closed", choices=("closed", "open", "all"))
        p.add_argument("--categories", default=None)
        p.add_argument("--workers", type=int, default=8)
        p.set_defaults(fn=fn)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

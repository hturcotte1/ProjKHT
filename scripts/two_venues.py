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


# ------------------------------------------------------------------- table
def cmd_table(args: argparse.Namespace) -> None:
    """One row per US market-day with a real book and a polymarket.com price at least an hour older."""
    pairs = pd.read_parquet(TWO / "pairs.parquet")
    m, _ = us_meta()
    h = pd.concat([pd.read_parquet(p) for p in sorted((US / "history").glob("*.parquet"))], ignore_index=True)
    h = h.merge(pairs[["slug", "intl_id", "event_id", "category", "yes_settle", "end_ts", "intl_volume", "rule"]], on="slug")
    h["period"] = (h["ts"] - 1) // 86_400
    h = h.sort_values(["slug", "ts"]).drop_duplicates(["slug", "period"], keep="last")
    n_all = len(h)
    tick = m.set_index("slug")["tick"].reindex(h["slug"]).fillna(0.01).to_numpy()
    spread = h["yes_ask"] + h["no_ask"] - 1.0
    lo, hi = 0.015, 0.985                                   # the filter of docs/06, section 7
    real = ((h["yes_ask"] >= lo) & (h["yes_ask"] <= hi) & (h["no_ask"] >= lo) & (h["no_ask"] <= hi) & (spread >= tick - 1e-9) & (spread <= 0.20))
    h = h[real].copy()
    h["spread"] = spread[real]
    px = pd.concat([pd.read_parquet(p) for p in sorted((TWO / "prices").glob("*.parquet"))], ignore_index=True)
    px = px.rename(columns={"ts": "intl_ts", "price": "P"}).sort_values("intl_ts")
    h["cut"] = h["ts"] - HOUR                                # nothing newer than an hour before the US quote
    h = h.sort_values("cut")
    t = pd.merge_asof(h, px, left_on="cut", right_on="intl_ts", by="intl_id", direction="backward", tolerance=23 * HOUR)
    with_price = t["P"].notna()
    log(f"paired markets: {len(pairs):,}; their market-days: {n_all:,}; with a real US book: {len(h):,} in {h['slug'].nunique():,} markets; "
        f"and a polymarket.com price 1 to 24 hours older: {int(with_price.sum()):,} in {t.loc[with_price, 'slug'].nunique():,} markets")
    t = t[with_price].sort_values(["slug", "ts"]).reset_index(drop=True)
    a, b, P = t["yes_ask"].to_numpy(), t["no_ask"].to_numpy(), t["P"].to_numpy()
    t["mid"] = (a + 1.0 - b) / 2.0
    t["gap_yes"] = P - a - taker_fee_per_share(a)
    t["gap_no"] = (1.0 - P) - b - taker_fee_per_share(b)
    t["settle_day"] = np.floor(t["end_ts"] / 86_400)
    t.to_parquet(CACHE / "two_venues.parquet", index=False)
    print(t.groupby("category").agg(markets=("slug", "nunique"), events=("event_id", "nunique"), days=("slug", "size")).to_string())
    d = t["P"] - t["mid"]
    log(f"polymarket.com price minus the middle of the US book: mean {100 * d.mean():+.2f}c, median {100 * d.median():+.2f}c, "
        f"sd {100 * d.std():.2f}c; 3c or more apart on {100 * (d.abs() >= 0.03).mean():.1f}% of days, 10c or more on {100 * (d.abs() >= 0.10).mean():.1f}%")


# -------------------------------------------------------------------- tests
def slope(x: np.ndarray, y: np.ndarray, cluster: np.ndarray) -> tuple[float, float, int]:
    """OLS slope of y on x (with an intercept) and its cluster-robust standard error."""
    x0, y0 = x - x.mean(), y - y.mean()
    sxx = float(np.dot(x0, x0))
    beta = float(np.dot(x0, y0)) / sxx
    resid = y0 - beta * x0
    _, inv = np.unique(cluster, return_inverse=True)
    g = int(inv.max()) + 1
    s = np.bincount(inv, weights=x0 * resid, minlength=g)
    se = (g / (g - 1) * float(np.dot(s, s))) ** 0.5 / sxx
    return beta, se, g


def first_gap(t: pd.DataFrame, g: float, hi: float | None = None) -> pd.DataFrame:
    """T6-B: each market's first day with a gap of at least ``g`` on either side, as a purchase of that side."""
    gap = np.maximum(t["gap_yes"].to_numpy(), t["gap_no"].to_numpy())
    k = t[gap >= g].drop_duplicates("slug", keep="first").copy()
    side_yes = k["gap_yes"].to_numpy() >= k["gap_no"].to_numpy()
    y = k["yes_settle"].to_numpy()
    ask = np.where(side_yes, k["yes_ask"], k["no_ask"])
    other = np.where(side_yes, k["no_ask"], k["yes_ask"])
    k["side"] = np.where(side_yes, "yes", "no")
    k["gap"] = np.where(side_yes, k["gap_yes"], k["gap_no"])
    k["cost"] = ask + taker_fee_per_share(ask)
    k["paid"] = np.where(side_yes, y, 1.0 - y)
    k["ret"] = (k["paid"] - k["cost"]) / k["cost"]
    k["cost_other"] = other + taker_fee_per_share(other)
    k["ret_other"] = ((1.0 - k["paid"]) - k["cost_other"]) / k["cost_other"]
    if hi is not None:
        k = k[k["gap"] < hi]
    return k


def delayed(t: pd.DataFrame, k: pd.DataFrame, g: float) -> pd.DataFrame:
    """The same purchases made one observation later (within three days), if the gap on that side is still at least ``g`` then."""
    nxt = t.copy()
    nxt["row"] = nxt.groupby("slug").cumcount()
    pos = nxt.merge(k[["slug", "ts", "side"]].rename(columns={"ts": "ts0"}), on="slug")
    first_row = pos[pos["ts"] == pos["ts0"]][["slug", "row"]].rename(columns={"row": "row0"})
    pos = pos.merge(first_row, on="slug")
    d = pos[(pos["row"] == pos["row0"] + 1) & (pos["ts"] - pos["ts0"] <= 3 * 86_400)].copy()
    side_yes = d["side"].to_numpy() == "yes"
    gap = np.where(side_yes, d["gap_yes"], d["gap_no"])
    d = d[gap >= g].copy()
    side_yes = d["side"].to_numpy() == "yes"
    ask = np.where(side_yes, d["yes_ask"], d["no_ask"])
    y = d["yes_settle"].to_numpy()
    d["cost"] = ask + taker_fee_per_share(ask)
    d["paid"] = np.where(side_yes, y, 1.0 - y)
    d["ret"] = (d["paid"] - d["cost"]) / d["cost"]
    return d


def score(k: pd.DataFrame, col: str = "ret", cost: str = "cost") -> dict:
    from kht.research import factory as fx

    if len(k) < 2:
        return {"n": len(k)}
    r, c = k[col].to_numpy(), k[cost].to_numpy()
    mean, z_ev = fx.floored(r, c, k["event_id"].to_numpy())
    _, z_day = fx.floored(r, c, k["settle_day"].to_numpy())
    return {"n": len(k), "events": k["event_id"].nunique(), "days": k["settle_day"].nunique(), "ret": mean, "z_event": z_ev, "z_day": z_day,
            "win": float((k["paid"] if col == "ret" else 1.0 - k["paid"]).mean()), "avg_cost": float(c.mean())}


def cmd_test(args: argparse.Namespace) -> None:
    from kht.research import factory as fx

    t = pd.read_parquet(CACHE / "two_venues.parquet")
    lines = ["The tests of docs/07_two_venues.md, section 3", f"observations: {len(t):,} market-days in {t['slug'].nunique():,} markets, {t['event_id'].nunique():,} events"]
    rows = []
    election_days = [np.floor(pd.Timestamp(d).timestamp() / 86_400) for d in ("2026-11-03", "2026-11-04", "2026-11-05")]
    election = t["settle_day"].isin(election_days)

    def add(test: str, sample: str, res: dict) -> None:
        rows.append({"test": test, "sample": sample, **res})

    # ---- T6-B
    for g in (0.01, 0.02, 0.03, 0.05, 0.10):
        k = first_gap(t, g)
        add("T6-B buy the cheap side", f"gap >= {100 * g:g}c", score(k))
        add("T6-B the other side", f"gap >= {100 * g:g}c", score(k, "ret_other", "cost_other"))
    k3 = first_gap(t, 0.03)
    add("T6-B buy the cheap side", "gap 3c to 10c", score(k3[k3["gap"] < 0.10]))
    add("T6-B buy the cheap side", "gap >= 3c, bought one observation later", score(delayed(t, k3, 0.03)))
    add("T6-B buy the cheap side", "gap >= 3c, without markets settled 3-5 November", score(first_gap(t[~election], 0.03)))
    for side in ("yes", "no"):
        add("T6-B buy the cheap side", f"gap >= 3c, the cheap side is {side}", score(k3[k3["side"] == side]))
    for cat, kk in k3.groupby("category"):
        add("T6-B buy the cheap side", f"gap >= 3c, {cat}", score(kk))
    big = k3["intl_volume"] >= 10_000
    add("T6-B buy the cheap side", "gap >= 3c, polymarket.com market traded $10,000 or more", score(k3[big]))
    add("T6-B buy the cheap side", "gap >= 3c, polymarket.com market traded less", score(k3[~big]))
    k3.to_csv(OUT / "tv_trades_3c.csv", index=False)

    # ---- T6-A
    diff = (t["P"] - t["mid"]).abs() >= 0.03
    a = t[diff].drop_duplicates("slug", keep="first").copy()
    y = a["yes_settle"].to_numpy()
    a["d"] = (a["mid"] - y) ** 2 - (a["P"] - y) ** 2
    for name, kk in (("first day 3c or more apart", a), ("the same, without markets settled 3-5 November", a[~a["settle_day"].isin(election_days)])):
        if len(kk) >= 2:
            m_, t_ev = fx.clustered(kk["d"].to_numpy(), kk["event_id"].to_numpy())
            _, t_day = fx.clustered(kk["d"].to_numpy(), kk["settle_day"].to_numpy())
            add("T6-A squared error of the US middle minus that of polymarket.com", name,
                {"n": len(kk), "events": kk["event_id"].nunique(), "days": kk["settle_day"].nunique(), "ret": m_, "z_event": t_ev, "z_day": t_day,
                 "win": float((kk["d"] > 0).mean())})

    # ---- T6-C
    s = t.sort_values(["slug", "period"])
    nxt = s.groupby("slug")[["period", "mid", "P"]].shift(-1)
    ok = (nxt["period"] - s["period"]) == 1
    c = pd.DataFrame({"gap": (s["P"] - s["mid"])[ok], "d_us": (nxt["mid"] - s["mid"])[ok], "d_intl": (nxt["P"] - s["P"])[ok], "event_id": s["event_id"][ok]})
    for name, col in (("next day's change in the US middle on today's (polymarket.com - US)", "d_us"), ("next day's change in polymarket.com on the same", "d_intl")):
        beta, se, g = slope(c["gap"].to_numpy(), c[col].to_numpy(), c["event_id"].to_numpy())
        add("T6-C who moves", name, {"n": len(c), "events": g, "ret": beta, "z_event": beta / se})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "tv_tests.csv", index=False)
    show = res.copy()
    pct = show["test"].str.startswith("T6-B")
    show.loc[pct, "ret"] = 100 * show.loc[pct, "ret"]
    lines.append("T6-B: 'ret' is the mean return in percent; T6-A: mean difference of squared errors (positive: polymarket.com closer); T6-C: slope")
    text = "\n".join(lines) + "\n\n" + show.round(3).to_string(index=False) + "\n"
    (OUT / "two_venues_output.txt").write_text(text)
    print(text)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pairs").set_defaults(fn=cmd_pairs)
    p = sub.add_parser("prices")
    p.add_argument("--bucket", type=int, default=HOUR)
    p.set_defaults(fn=cmd_prices)
    sub.add_parser("table").set_defaults(fn=cmd_table)
    sub.add_parser("test").set_defaults(fn=cmd_test)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

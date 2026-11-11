"""The last minutes of settled crypto markets on Polymarket US: test L1 on history (docs/11_crypto_us.md, section 5).

    python scripts/lasttick_history.py fetch     # terms, result, last quotes and final volume of each settled market -> data/us_crypto/lasttick/
    python scripts/lasttick_history.py index     # the index a quarter of an hour before each end -> data/us_crypto/lasttick_index.parquet
    python scripts/lasttick_history.py run       # the rule of L1 on it -> reports/research/lth_*

The history has no sizes and about one stored price in fifty was never in
a book (docs/06, section 7). It says how often the orders L1 trades against
were there and whether a result that was out of reach ever came in. The
live recorder (kht us-lasttick) is what measures the trade.

``run`` needs config/lasttick_reach.json, which scripts/lasttick_reach.py
writes and which is committed before this history is read.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from kht.api.polymarket_us import PolymarketUS  # noqa: E402
from kht.trading.us_lasttick import terms  # noqa: E402
from kht.trading.us_recorder import _amount, _num  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 300)
DATA = ROOT / "data" / "us_crypto"
OUT = ROOT / "reports" / "research"
SCOPE = re.compile(r"-(?:above|range)-(?:day|wk)-|-hit-[hl]-[wm]-|-updown-(?:1h|1d)-")
BEFORE = 26 * 60               # quotes are kept from this long before a market's end
LAST = pd.Timestamp("2026-11-11").timestamp()        # markets ending from 11 November on are left to the live recorder


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def universe() -> pd.DataFrame:
    m = pd.read_parquet(DATA / "markets_crypto.parquet")
    m = m[m["slug"].str.contains(SCOPE) & m["yes_settle"].notna() & (m["end_ts"] < LAST)]
    return m[["slug", "yes_settle", "end_ts"]].sort_values("slug").reset_index(drop=True)


def client(rate: float) -> PolymarketUS:
    from kht.api.http import Http

    return PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": rate}))


# ------------------------------------------------------------------- fetch
def cmd_fetch(args: argparse.Namespace) -> None:
    us = client(args.rate)
    dest = DATA / "lasttick"
    dest.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    for p in dest.glob("*.parquet"):
        done |= set(pd.read_parquet(p, columns=["slug"])["slug"])
    u = universe()
    todo = u[~u["slug"].isin(done)]
    log(f"fetch: {len(u):,} settled markets in scope, {len(todo):,} to fetch")

    def one(r) -> dict | None:
        try:
            raw = us.market(r.slug)
            t = terms(raw)
            if t is None:
                return {"slug": r.slug, "kind": ""}
            ap = raw.get("assetPriceTerms") or {}
            row = {**t, "yes_settle": float(r.yes_settle), "settlement_price": _amount(ap.get("settlementPrice")), "closed_at": str(raw.get("endDate") or "")}
            pts = us.price_history_window(r.slug, int(t["end"] - BEFORE), int(t["end"] + 120))
            row["quotes"] = json.dumps(pts)
            stats = (us.book(r.slug) or {}).get("stats") or {}
            row.update(traded=_num(stats.get("sharesTraded")), last=_amount(stats.get("lastTradePx")), low=_amount(stats.get("lowPx")), high=_amount(stats.get("highPx")))
            return row
        except Exception:
            return None                                    # fetched again on the next run

    buf: list[dict] = []
    part, t0, n = 0, time.time(), 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(one, list(todo.itertuples())):
            n += 1
            if row is not None:
                buf.append(row)
            if len(buf) >= 1_000:
                pd.DataFrame(buf).to_parquet(dest / f"lt_{int(time.time())}_{part}.parquet", index=False)
                part, buf = part + 1, []
            if n % 1000 == 0:
                rate = n / (time.time() - t0)
                log(f"fetch: {n:,}/{len(todo):,} ({rate:.1f}/s, about {(len(todo) - n) / rate / 60:.0f} minutes left)")
    if buf:
        pd.DataFrame(buf).to_parquet(dest / f"lt_{int(time.time())}_{part}.parquet", index=False)
    log(f"fetch: finished {n:,} in {time.time() - t0:.0f}s")


def fetched() -> pd.DataFrame:
    f = pd.concat([pd.read_parquet(p) for p in sorted((DATA / "lasttick").glob("*.parquet"))], ignore_index=True).drop_duplicates("slug")
    return f[f["kind"] != ""].reset_index(drop=True)


# ------------------------------------------------------------------- index
PRODUCT = {"btc": "cpc", "eth": "cpceth", "sol": "cpcsol", "xrp": "cpcxrp"}


def quarter_slug(coin: str, start: float) -> str:
    """The 15-minute up-or-down market of ``coin`` that starts at ``start``: its price to beat is the index then."""
    return f"{PRODUCT[coin]}-{coin}-updown-15m-{pd.Timestamp(start, unit='s').strftime('%Y-%m-%d-%H%M')}z"


def cmd_index(args: argparse.Namespace) -> None:
    us = client(args.rate)
    f = fetched()
    want = f[["coin", "end"]].drop_duplicates()
    want["at"] = want["end"] - 900.0
    path = DATA / "lasttick_index.parquet"
    have = pd.read_parquet(path) if path.exists() else pd.DataFrame(columns=["coin", "at", "level", "slug"])
    todo = want.merge(have[["coin", "at"]], on=["coin", "at"], how="left", indicator=True)
    todo = todo[todo["_merge"] == "left_only"]
    log(f"index: {len(want):,} ends, {len(todo):,} to look up")

    def one(r) -> dict:
        slug = quarter_slug(r.coin, r.at)
        try:
            raw = us.market(slug)
            return {"coin": r.coin, "at": r.at, "level": _amount((raw.get("assetPriceTerms") or {}).get("priceToBeat")), "slug": slug}
        except Exception:
            return {"coin": r.coin, "at": r.at, "level": None, "slug": slug}

    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(one, list(todo.itertuples())))
    out = pd.concat([have, pd.DataFrame(rows)], ignore_index=True) if rows else have
    out.to_parquet(path, index=False)
    log(f"index: {int(out['level'].notna().sum()):,} of {len(out):,} ends have an index level a quarter of an hour before")


# --------------------------------------------------------------------- run
AT = 900                       # the one moment the history is read at: a quarter of an hour before the end
LATER = (600, 300, 120)        # and where the order traded against is looked for again


def stored_book(points: list, ts: float) -> dict | None:
    """The book the price history stored for the moment ``ts``: the point labelled a minute earlier (docs/11, section 3).

    The history gives the best offer of "Yes" and one minus its best bid.
    When a side of the book was empty it gives the last trade in its place,
    which shows as a spread under one tick. Such a point is not a book.
    """
    for label, yes, no in points:
        if abs(label - (ts - 60.0)) < 1.0:
            bid, ask = round(1.0 - no, 4), round(yes, 4)
            if ask - bid < 0.01 - 1e-9:
                return None
            return {"bid1": bid if 0.01 - 1e-9 <= bid <= 0.99 + 1e-9 else None, "bid_qty1": 1.0, "ask1": ask if 0.01 - 1e-9 <= ask <= 0.99 + 1e-9 else None, "ask_qty1": 1.0}
    return None


def brake_history(closes: dict[str, pd.Series], coin: str, ts: float) -> list[tuple[float, float]]:
    """Five-minute levels of the hour before ``ts`` for the brake, from outside minute prices (the exchange's own are not kept that far back).

    The level at a mark is the close of the minute that ends there.
    """
    c = closes.get(coin)
    if c is None:
        return []
    last = int(ts) // 300 * 300
    marks = np.arange(last - 3900, last + 1, 300)
    v = c.reindex(marks - 60)
    return [(float(m), float(x)) for m, x in zip(marks, v.to_numpy()) if np.isfinite(x)]


def score(f: pd.DataFrame, idx: pd.Series, reach: dict, brake: dict | None, closes: dict[str, pd.Series]) -> pd.DataFrame:
    """One yardstick on every fetched market, at one reading a quarter of an hour before its end."""
    from kht.trading import lasttick_rule as rule

    rows = []
    for m in f.to_dict("records"):
        end = float(m["end"])
        closed = pd.Timestamp(m["closed_at"]).timestamp() if m.get("closed_at") else np.nan
        row = {"slug": m["slug"], "coin": m["coin"], "kind": m["kind"], "horizon": m["horizon"], "end": end, "yes_settle": m["yes_settle"], "traded": m.get("traded")}
        if np.isfinite(closed) and closed < end - AT:
            rows.append({**row, "fate": "settled before its last quarter of an hour"})      # a "hit" market that was hit
            continue
        level = idx.get((m["coin"], end - AT))
        level = float(level) if level is not None and np.isfinite(level) else None
        points = json.loads(m["quotes"]) if m.get("quotes") else []
        ts = end - AT
        history = brake_history(closes, m["coin"], ts) if brake is not None else None
        g = rule.gap(m, level) if level is not None else None
        r = rule.reach_for(reach, m["coin"], AT / 60.0 + 1.0)
        clear = brake is None or rule.brake_state(history, ts, brake.get(m["coin"])) == "clear"
        if g is not None and r is not None and g[0] > r and clear:
            # out of reach and not braked: did the result hold, whatever the book showed?
            row.update(out_of_reach=True, held=(m["yes_settle"] == (1.0 if g[1] == "yes" else 0.0)), as_things_stood=g[1], gap=g[0], reach=r)
        book = stored_book(points, ts)
        trade, why = rule.decide(m, book or {}, ts, level, ts, reach, brake, history)
        if why.startswith("out of reach, nobody") and book is None and points:
            why = "out of reach, no real book stored"
        elif why.startswith("out of reach, nobody") and not points:
            why = "out of reach, no quote stored at all"
        row["fate"] = why
        if trade is not None:
            row.update(side=trade["side"], price=trade["price"], premium=trade["premium"], pnl=rule.pnl(trade, float(m["yes_settle"])))
            for later in LATER:                                  # is the same price still there nearer the end?
                b2 = stored_book(points, end - later)
                key = "bid1" if trade["side"] == "sell" else "ask1"
                row[f"still_{later // 60}m"] = bool(b2 and b2.get(key) is not None and abs(b2[key] - trade["price"]) < 1e-9)
        rows.append(row)
    res = pd.DataFrame(rows)
    for col in ("out_of_reach", "held", "gap", "reach", "side", "price", "premium", "pnl", "still_10m", "still_5m", "still_2m"):
        if col not in res:
            res[col] = np.nan
    res["group"] = res["kind"].str.replace("_", " ") + " (" + res["horizon"] + ")"
    return res


def describe(name: str, res: pd.DataFrame) -> list[str]:
    lines = [f"===== {name} ====="]
    fates = res.groupby(["group", "fate"]).size().unstack(fill_value=0)
    lines += ["what became of each market, by kind", fates.T.to_string(), ""]
    oor = res[res["out_of_reach"] == True]  # noqa: E712
    lines.append(f"results that were out of reach by the rule, whatever the book showed: {len(oor):,}; of these the result changed in "
                 f"{int((~oor['held'].astype(bool)).sum()) if len(oor) else 0:,}")
    if len(oor):
        lines += [oor.groupby("group").agg(out_of_reach=("slug", "size"), ends=("end", "nunique"), changed=("held", lambda s: int((~s.astype(bool)).sum())),
                                           median_gap=("gap", "median"), reach=("reach", "median")).round(4).to_string(), ""]
        changed = oor[~oor["held"].astype(bool)]
        if len(changed):
            lines += ["the results that changed", changed[["slug", "as_things_stood", "gap", "reach", "yes_settle"]].to_string(index=False), ""]
    tr = res[res["fate"] == "trade"]
    lines.append(f"trades (an order to trade against was stored at that moment): {len(tr):,}; lost {int((tr['pnl'] < 0).sum()):,}; "
                 f"premium a contract {100 * tr['premium'].mean() if len(tr) else 0:.3f} cents; result a contract {100 * tr['pnl'].mean() if len(tr) else 0:.3f} cents")
    if len(tr):
        g = tr.groupby(["group", "coin"]).agg(trades=("slug", "size"), sales=("side", lambda s: int((s == "sell").sum())), ends=("end", "nunique"),
                                              price=("price", "mean"), premium_cents=("premium", lambda s: 100 * s.mean()), lost=("pnl", lambda s: int((s < 0).sum())),
                                              result_cents=("pnl", lambda s: 100 * s.mean()), never_traded=("traded", lambda s: float((s.fillna(0) == 0).mean())),
                                              still_10m=("still_10m", "mean"), still_5m=("still_5m", "mean"), still_2m=("still_2m", "mean")).round(3)
        lines += [g.to_string(), ""]
        day = tr[tr["horizon"].isin(["daily", "weekly", "monthly", "1d"])].assign(day=lambda d: pd.to_datetime(d["end"], unit="s").dt.strftime("%m-%d"))
        if len(day):
            per_day = day.groupby("day").agg(levels=("slug", "size"), lost=("pnl", lambda s: int((s < 0).sum())))
            lines += [f"daily, weekly and monthly settlements: levels with an order to trade against, by day (days: {len(per_day)}; median {per_day['levels'].median():.0f} a day)",
                      per_day.T.to_string(), ""]
    lost = tr[tr["pnl"] < 0]
    if len(lost):
        lines += ["the trades that lost", lost[["slug", "side", "price", "gap", "reach", "pnl"]].to_string(index=False), ""]
    return lines


def cmd_run(args: argparse.Namespace) -> None:
    from kht.trading import lasttick_rule as rule

    config = ROOT / "config" / "lasttick_reach.json"
    strict = rule.load_reach(config)
    recent, brake = rule.load_recent(config)
    f = fetched()
    idx = pd.read_parquet(DATA / "lasttick_index.parquet").dropna(subset=["level"]).set_index(["coin", "at"])["level"]
    closes = {}
    for coin in sorted(f["coin"].unique()):
        path = ROOT / "data" / "crypto" / f"minute_{coin}.parquet"
        if path.exists():
            closes[coin] = pd.read_parquet(path, columns=["t", "close"]).drop_duplicates("t").set_index("t")["close"]
    ends = f[["coin", "end"]].drop_duplicates()
    with_level = int(pd.MultiIndex.from_arrays([ends["coin"], ends["end"] - AT]).isin(idx.index).sum())
    lines = ["Test L1 on the history of settled crypto markets (docs/11, section 5, item 3): one reading a market, a quarter of an hour before its end",
             f"markets fetched: {len(f):,}; ends: {len(ends):,}; ends with an index level a quarter of an hour before: {with_level:,}",
             "the history has no sizes: every trade here is one contract", ""]
    for name, tag, reach, brk in (("L1-recent: the reach of 2023 to 2026, with the brake", "recent", recent, brake),
                                  ("L1-strict: the reach of the worst year since 2020, as first written", "strict", strict, None)):
        res = score(f, idx, reach, brk, closes)
        res.to_parquet(DATA / f"lasttick_history_{tag}.parquet", index=False)
        res[res["fate"] == "trade"].to_csv(OUT / f"lth_trades_{tag}.csv", index=False)
        res.groupby(["group", "fate"]).size().unstack(fill_value=0).to_csv(OUT / f"lth_fates_{tag}.csv")
        lines += describe(name, res) + [""]
    text = "\n".join(lines) + "\n"
    (OUT / "lasttick_history_output.txt").write_text(text)
    print(text)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("fetch", cmd_fetch), ("index", cmd_index)):
        p = sub.add_parser(name)
        p.add_argument("--workers", type=int, default=8)
        p.add_argument("--rate", type=float, default=8.0, help="requests a second")
        p.set_defaults(fn=fn)
    sub.add_parser("run").set_defaults(fn=cmd_run)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

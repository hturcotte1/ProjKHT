"""What being run over cost a resting order before past games (docs/09_sports_rewards.md, section 4).

    python scripts/rest_history.py paths [--shard i/n]   # minute-by-minute best prices, six hours before each game -> data/us_sports/paths/
    python scripts/rest_history.py run                   # the measure fixed in docs/09 -> reports/research/rh_*

The exchange keeps the best price on each side of every book, minute by
minute, but no sizes and no trades. So this can only see one thing: a
resting order that the whole market moved through. That is the costly kind
of fill. Everything is public data.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.api.polymarket_us import PolymarketUS

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 200)
ROOT = Path(__file__).resolve().parents[1]
SP = ROOT / "data" / "us_sports"
OUT = ROOT / "reports" / "research"
LAST = pd.Timestamp("2026-11-11").timestamp()
WINDOW, PULL, STEP = 6 * 3600, 600, 120      # as the paper account of section 5: six hours, pulled ten minutes before, moved every two minutes
STALE = 300                                  # a reading uses the last stored minute, if it is at most this old
MAX_WIDTH = 0.10                             # nothing rests in a book wider than this
SIZE = 100                                   # contracts on each side
# the leagues of the programmes named "thin" in section 5, as the reward schedule listed them on 11 November
GROUPS = {"ITF": ("itfme", "itfwo", "itfm", "itfw"), "UTR": ("utr",), "doubles": ("atpdb", "wtadb"), "darts": ("modus",), "beach volleyball": ("acw",)}
FORMULA = {"ITF": 1.62, "UTR": 2.15, "doubles": 1.89, "darts": 1.24, "beach volleyball": 1.63}   # the one look of section 3, dollars a game


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def games() -> pd.DataFrame:
    m = pd.read_parquet(SP / "markets_sports.parquet")
    m = m[(m["market_type"] == "moneyline") & m["game_start_ts"].notna() & m["yes_settle"].notna() & (m["game_start_ts"] < LAST)].copy()
    m["league"] = m["slug"].str.split("-").str[1]
    group = {lg: name for name, leagues in GROUPS.items() for lg in leagues}
    m["group"] = m["league"].map(group)
    return m[m["group"].notna()]


def cmd_paths(args: argparse.Namespace) -> None:
    from kht.api.http import Http

    pm = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": args.rate}))
    m = games().sort_values("market_id")
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        m = m.iloc[i::n]
    dest = SP / "paths"
    dest.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    for p in dest.glob("*.parquet"):
        done |= set(pd.read_parquet(p, columns=["slug"])["slug"])
    todo = m[~m["slug"].isin(done)]
    log(f"paths: {len(m):,} games, {len(todo):,} to fetch")

    def one(r) -> dict | None:
        gs = int(r.game_start_ts)
        try:
            pts = pm.price_history_window(r.slug, gs - WINDOW - STALE, gs)
        except Exception:
            return None                                   # fetched on the next run
        a = np.array(pts, dtype=float) if pts else np.zeros((0, 3))
        return {"slug": r.slug, "ts": a[:, 0].astype(np.int64), "yes": a[:, 1].astype(np.float32), "no": a[:, 2].astype(np.float32)}

    buf: list[dict] = []
    part, t0, n = 0, time.time(), 0
    tag = (args.shard or "0/1").replace("/", "of")
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(one, list(todo.itertuples())):
            n += 1
            if row is not None:
                buf.append(row)
            if len(buf) >= 2_000:
                pd.DataFrame(buf).to_parquet(dest / f"p_{tag}_{int(time.time())}_{part}.parquet", index=False)
                part, buf = part + 1, []
            if n % 5000 == 0:
                rate = n / (time.time() - t0)
                log(f"paths: {n:,}/{len(todo):,} ({rate:.1f}/s, eta {(len(todo) - n) / rate / 60:.0f} min)")
    if buf:
        pd.DataFrame(buf).to_parquet(dest / f"p_{tag}_{int(time.time())}_{part}.parquet", index=False)
    log(f"paths: finished {n:,} in {time.time() - t0:.0f}s")


def simulate(ts: np.ndarray, yes: np.ndarray, no: np.ndarray, start: float, tick: float) -> dict:
    """One game: orders at the best prices, moved every two minutes; filled when the next reading has gone through them."""
    out = {"readings": 0, "quoted": 0, "blind": 0, "bid_px": np.nan, "ask_px": np.nan, "bid_lead": np.nan, "ask_lead": np.nan, "mid_last": np.nan}
    if len(ts) == 0:
        return out
    grid = np.arange(start - WINDOW, start - PULL + 1, STEP)
    idx = np.searchsorted(ts, grid, side="right") - 1
    seen = (idx >= 0) & (grid - ts[np.clip(idx, 0, None)] <= STALE)
    k = np.clip(idx, 0, None)
    ask, bid = yes[k].astype(float), 1.0 - no[k].astype(float)
    width = ask - bid
    # a book with real prices on both sides (docs/06, section 7); only one no wider than MAX_WIDTH is rested in
    real = seen & (ask >= 0.015) & (ask <= 0.985) & (bid >= 0.015) & (bid <= 0.985) & (width >= tick - 1e-9) & (width <= 0.20 + 1e-9)
    rest = real & (width <= MAX_WIDTH + 1e-9)
    out["readings"], out["quoted"] = int(seen.sum()), int(rest.sum())
    if rest.any():
        last = np.flatnonzero(rest)[-1]
        out["mid_last"] = (ask[last] + bid[last]) / 2.0
    here, nxt = rest[:-1], real[1:]
    out["blind"] = int((here & ~nxt).sum())                 # we were resting, and the next reading cannot be read
    bid_hit = np.flatnonzero(here & nxt & (ask[1:] <= bid[:-1] + 1e-9))
    ask_hit = np.flatnonzero(here & nxt & (bid[1:] >= ask[:-1] - 1e-9))
    if len(bid_hit):
        out["bid_px"], out["bid_lead"] = bid[bid_hit[0]], start - grid[bid_hit[0] + 1]
    if len(ask_hit):
        out["ask_px"], out["ask_lead"] = ask[ask_hit[0]], start - grid[ask_hit[0] + 1]
    return out


def clustered(values: np.ndarray, clusters: np.ndarray) -> tuple[float, float]:
    n, mean = len(values), float(values.mean())
    _, inv = np.unique(clusters, return_inverse=True)
    g = int(inv.max()) + 1
    if n < 2 or g < 2:
        return mean, float("nan")
    s = np.bincount(inv, weights=values - mean, minlength=g)
    var = g / (g - 1) * float(np.dot(s, s)) / n**2
    return mean, (mean / var**0.5 if var > 0 else float("nan"))


def cmd_run(args: argparse.Namespace) -> None:
    m = games().set_index("slug")
    rows = []
    for p in sorted((SP / "paths").glob("*.parquet")):
        for r in pd.read_parquet(p).itertuples():
            if r.slug not in m.index:
                continue
            g = m.loc[r.slug]
            tick = float(g["tick"]) if pd.notna(g["tick"]) else 0.01
            rows.append({"slug": r.slug, **simulate(np.asarray(r.ts, dtype=float), np.asarray(r.yes), np.asarray(r.no), float(g["game_start_ts"]), tick)})
    t = pd.DataFrame(rows).drop_duplicates("slug").set_index("slug").join(m[["group", "league", "game_start_ts", "yes_settle"]])
    t["day"] = np.floor(t["game_start_ts"] / 86_400)
    t["month"] = pd.to_datetime(t["game_start_ts"], unit="s").dt.strftime("%Y-%m")
    s = t["yes_settle"].astype(float)
    t["bid_pnl"] = np.where(t["bid_px"].notna(), SIZE * (s - t["bid_px"]), 0.0)
    t["ask_pnl"] = np.where(t["ask_px"].notna(), SIZE * (t["ask_px"] - s), 0.0)
    t["pnl"] = t["bid_pnl"] + t["ask_pnl"]
    t["pnl_mid"] = np.where(t["bid_px"].notna(), SIZE * (t["mid_last"] - t["bid_px"]), 0.0) + np.where(t["ask_px"].notna(), SIZE * (t["ask_px"] - t["mid_last"]), 0.0)
    t["fills"] = t["bid_px"].notna().astype(int) + t["ask_px"].notna().astype(int)
    q = t[t["quoted"] > 0]
    lines = ["Being run over before past games: orders of 100 contracts at the best price on each side, moved every two minutes, from six hours to ten minutes before the start",
             f"games in the leagues of the thin programmes: {len(m):,}; with stored prices: {int((t['readings'] > 0).sum()):,}; with a book to rest in at some reading: {len(q):,}",
             f"hours rested, all games: {q['quoted'].sum() * STEP / 3600:,.0f}; readings after which the next could not be read: {100 * q['blind'].sum() / max(q['quoted'].sum(), 1):.1f}% of those rested"]
    out = []
    for name, grp in [("all", q)] + [(k, q[q["group"] == k]) for k in GROUPS]:
        if not len(grp):
            continue
        mean, z = clustered(grp["pnl"].to_numpy(), grp["day"].to_numpy())
        mean_mid, z_mid = clustered(grp["pnl_mid"].to_numpy(), grp["day"].to_numpy())
        filled = grp[grp["fills"] > 0]
        out.append({"programme": name, "games": len(grp), "hours_rested_a_game": grp["quoted"].mean() * STEP / 3600, "games_filled_pct": 100 * (grp["fills"] > 0).mean(),
                    "fills_a_game": grp["fills"].mean(), "cents_a_filled_contract": 100 * filled["pnl"].sum() / (SIZE * max(filled["fills"].sum(), 1)),
                    "dollars_a_game": mean, "z_by_day": z, "dollars_a_game_at_last_mid": mean_mid, "z_at_last_mid": z_mid,
                    "formula_reward_a_game": FORMULA.get(name, np.nan)})
    res = pd.DataFrame(out)
    res.round(4).to_csv(OUT / "rh_by_programme.csv", index=False)
    by_month = q.groupby(["group", "month"]).agg(games=("pnl", "size"), games_filled_pct=("fills", lambda x: 100 * (x > 0).mean()), dollars_a_game=("pnl", "mean"),
                                                 dollars_a_game_at_last_mid=("pnl_mid", "mean")).reset_index()
    by_month.round(4).to_csv(OUT / "rh_by_month.csv", index=False)
    lead = pd.concat([t["bid_lead"].dropna(), t["ask_lead"].dropna()]) / 3600.0
    when = pd.cut(lead, [0, 0.5, 1, 2, 3, 4, 5, 6.01]).value_counts(sort=False)
    lines += ["", "what the fills made, held to settlement, for each game rested in (negative: a cost)", res.round(3).to_string(index=False),
              "", "by month", by_month.round(3).to_string(index=False),
              "", "hours before the start at which the fills happened", when.to_string()]
    text = "\n".join(lines) + "\n"
    (OUT / "rest_history_output.txt").write_text(text)
    print(text)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("paths")
    p.add_argument("--shard", default=None)
    p.add_argument("--workers", type=int, default=10)
    p.add_argument("--rate", type=float, default=11.0, help="requests a second; the paper account's runs use the same public limit from another machine")
    p.set_defaults(fn=cmd_paths)
    sub.add_parser("run").set_defaults(fn=cmd_run)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

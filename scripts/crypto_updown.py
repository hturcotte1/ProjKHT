"""Up-or-down crypto markets on Polymarket US: the search of docs/11_crypto_us.md, section 7.

    python scripts/crypto_updown.py paths [--shard i/n]   # minute prices of every settled market -> data/us_crypto/updown/
    python scripts/crypto_updown.py build                 # the decision table -> data/cache/crypto_updown.parquet
    python scripts/crypto_updown.py run [--placebo 20]    # the grid and the judge -> reports/research/ud_*
    python scripts/crypto_updown.py table                 # asking price against how often that side won, by minutes left

A market's stored minute prices are read as the book at the end of each
minute. A rule looks at the book with M minutes of the window left and
buys one side at its asking price. Everything is public data.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import time
import warnings
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from kht.api.polymarket_us import PolymarketUS
from kht.research import factory as fx

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
pd.set_option("display.max_colwidth", 90)
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "us_crypto"
OUT = ROOT / "reports" / "research"
CACHE = ROOT / "data" / "cache"
LENGTH = {"5m": 300, "15m": 900, "1h": 3600}
LEFT = {"5m": (4, 3, 2, 1), "15m": (12, 8, 5, 3, 2, 1), "1h": (45, 30, 15, 10, 5, 3, 2, 1)}     # minutes of the window left at the purchase
COINS = ("all", "btc", "others")
SIDES = ("up", "down")
SPREADS = (0.01, 0.03, None)            # None: any real book (up to 10c)
CONDITIONS = ("none", "prev same", "prev other", "led", "not led")
SPLIT = pd.Timestamp("2026-11-03").timestamp()
LAST = pd.Timestamp("2026-11-11").timestamp()
THETA = 0.095
SLUG = re.compile(r"^cpc[a-z]*-([a-z]+)-updown-(5m|15m|1h)-(\d{4}-\d{2}-\d{2})-(\d{2})(\d{2})z$")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def markets() -> pd.DataFrame:
    """Every settled up-or-down market in scope, with its window read from its name."""
    m = pd.read_parquet(DATA / "markets_crypto.parquet")
    m = m[m["yes_settle"].isin([0.0, 1.0])]
    got = m["slug"].str.extract(SLUG)
    m = m[got[0].notna()].copy()
    got = got.loc[m.index]
    m["coin"], m["length"] = got[0], got[1]
    m["w0"] = (pd.to_datetime(got[2] + " " + got[3] + ":" + got[4]).astype("int64") // 10**9).astype(float)
    m["w1"] = m["w0"] + m["length"].map(LENGTH)
    m = m[m["w1"] < LAST]
    return m[["slug", "coin", "length", "w0", "w1", "yes_settle"]].sort_values(["length", "coin", "w0"]).reset_index(drop=True)


# ------------------------------------------------------------------- paths
def cmd_paths(args: argparse.Namespace) -> None:
    from kht.api.http import Http

    us = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": args.rate}))
    m = markets()
    dest = DATA / "updown"
    dest.mkdir(parents=True, exist_ok=True)
    if args.check:
        # the window read from a market's name against the window in its definition, on a sample
        bad = 0
        for r in m.sample(args.check, random_state=7).itertuples():
            t = (us.market(r.slug).get("assetPriceTerms") or {})
            w0, w1 = pd.Timestamp(t.get("windowStart")).timestamp(), pd.Timestamp(t.get("windowEnd")).timestamp()
            bad += int(abs(w0 - r.w0) > 1 or abs(w1 - r.w1) > 1)
        log(f"check: {args.check} names against their definitions, {bad} differ")
        return
    done: set[str] = set()
    for p in dest.glob("*.parquet"):
        done |= set(pd.read_parquet(p, columns=["slug"])["slug"])
    todo = m[~m["slug"].isin(done)]
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        todo = todo.iloc[i::n]
    log(f"paths: {len(m):,} settled markets, {len(todo):,} to fetch")

    def one(r) -> dict | None:
        try:
            return {"slug": r.slug, "points": json.dumps(us.price_history_window(r.slug, int(r.w0 - 180), int(r.w1 + 60)))}
        except Exception:
            return None                                   # fetched again on the next run

    buf: list[dict] = []
    part, t0, n = 0, time.time(), 0
    tag = (args.shard or "0/1").replace("/", "of")
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(one, list(todo.itertuples())):
            n += 1
            if row is not None:
                buf.append(row)
            if len(buf) >= 4_000:
                pd.DataFrame(buf).to_parquet(dest / f"p_{tag}_{int(time.time())}_{part}.parquet", index=False)
                part, buf = part + 1, []
            if n % 4000 == 0:
                rate = n / (time.time() - t0)
                log(f"paths: {n:,}/{len(todo):,} ({rate:.1f}/s, about {(len(todo) - n) / rate / 60:.0f} minutes left)")
    if buf:
        pd.DataFrame(buf).to_parquet(dest / f"p_{tag}_{int(time.time())}_{part}.parquet", index=False)
    log(f"paths: finished {n:,} in {time.time() - t0:.0f}s")


# ------------------------------------------------------------------- table
def book_at(points: dict[int, tuple[float, float]], moment: float) -> tuple[float, float] | None:
    """The asking prices of "Up" and "Down" at ``moment``: the stored point labelled a minute earlier, if it is a real book."""
    p = points.get(int(round(moment - 60.0)))
    if p is None:
        return None
    yes, no = p
    spread = yes + no - 1.0
    if not (0.01 - 1e-9 <= yes <= 0.99 + 1e-9 and 0.01 - 1e-9 <= no <= 0.99 + 1e-9 and 0.01 - 1e-9 <= spread <= 0.10 + 1e-9):
        return None
    return yes, no


def rows_for(m: dict, points: dict[int, tuple[float, float]], prev: float | None) -> list[dict]:
    """The decision rows of one market: one for each side at each of its purchase times that has a real book."""
    out = []
    w0, w1 = m["w0"], m["w1"]
    for left in LEFT[m["length"]]:
        moment = w1 - 60.0 * left
        b = book_at(points, moment)
        if b is None:
            continue
        yes, no = b
        mid = (yes + 1.0 - no) / 2.0
        # how the earlier minutes of this window stood: was "Up" the dearer side at each stored minute so far?
        earlier = [book_at(points, t) for t in np.arange(w0 + 60.0, moment - 1.0, 60.0)]
        earlier = [(e[0] + 1.0 - e[1]) / 2.0 for e in earlier if e is not None]
        for side, ask, fair, won in ((0, yes, mid, m["yes_settle"]), (1, no, 1.0 - mid, 1.0 - m["yes_settle"])):
            led = bool(earlier) and all((x > 0.5) if side == 0 else (x < 0.5) for x in earlier)
            as_side = 1.0 if side == 0 else 0.0                # what "Up" paid in a window that ended this side's way
            out.append({"slug": m["slug"], "coin": m["coin"], "length": m["length"], "left": left, "side": side, "ask": ask, "spread": yes + no - 1.0,
                        "fair": fair, "won": won, "prev_same": prev is not None and prev == as_side,
                        "prev_other": prev is not None and prev != as_side, "led": led, "not_led": bool(earlier) and not led,
                        "hour": float(np.floor(w1 / 3600.0)), "slot": f"{m['length']}-{int(w1)}", "split": 0 if w1 < SPLIT else 1})
    return out


def cmd_build(args: argparse.Namespace) -> None:
    m = markets()
    p = pd.concat([pd.read_parquet(f) for f in sorted((DATA / "updown").glob("*.parquet"))], ignore_index=True).drop_duplicates("slug")
    t = m.merge(p, on="slug")
    log(f"markets: {len(m):,}; with prices fetched: {len(t):,}")
    settle = {(r.coin, r.length, r.w1): r.yes_settle for r in m.itertuples()}        # how each window ended, to know the one before
    rows: list[dict] = []
    for r in t.to_dict("records"):
        pts = {int(a): (float(y), float(n)) for a, y, n in json.loads(r["points"])}
        rows += rows_for(r, pts, settle.get((r["coin"], r["length"], r["w0"])))
    f = pd.DataFrame(rows)
    CACHE.mkdir(parents=True, exist_ok=True)
    f.to_parquet(CACHE / "crypto_updown.parquet", index=False)
    log(f"table: {len(f):,} rows from {f['slug'].nunique():,} markets with a real book at one purchase time or more; "
        f"before 3 November {f.loc[f['split'] == 0, 'slug'].nunique():,}, from then {f.loc[f['split'] == 1, 'slug'].nunique():,}")
    print(f.groupby(["length", "left"])["slug"].nunique().unstack(fill_value=0).to_string())


# --------------------------------------------------------------------- run
class UpDown:
    """One length and purchase time as arrays, and the rules of section 7 evaluated on it."""

    def __init__(self, f: pd.DataFrame):
        self.n = len(f)
        self.ask = f["ask"].to_numpy(dtype=float)
        self.cost = self.ask + THETA * self.ask * (1.0 - self.ask)
        self.spread = f["spread"].to_numpy(dtype=float)
        self.won = f["won"].to_numpy(dtype=float)
        self.fair = f["fair"].to_numpy(dtype=float)
        self.side = f["side"].to_numpy()
        self.hour = f["hour"].to_numpy()
        self.split = f["split"].to_numpy()
        _, self.slot = np.unique(f["slot"].to_numpy(), return_inverse=True)
        coin = f["coin"].to_numpy()
        self.m_coin = {"all": np.ones(self.n, bool), "btc": coin == "btc", "others": coin != "btc"}
        self.m_side = {"up": self.side == 0, "down": self.side == 1}
        self.m_cond = {"none": np.ones(self.n, bool), "prev same": f["prev_same"].to_numpy(bool), "prev other": f["prev_other"].to_numpy(bool),
                       "led": f["led"].to_numpy(bool), "not led": f["not_led"].to_numpy(bool)}
        self.m_band = {b: (self.ask > b[0]) & (self.ask <= b[1]) for b in fx.BANDS}

    def specs(self):
        return list(product(COINS, SIDES, fx.BANDS, SPREADS, CONDITIONS))

    def trades(self, sp) -> np.ndarray:
        coin, side, band, w, cond = sp
        m = self.m_coin[coin] & self.m_side[side] & self.m_band[band] & self.m_cond[cond]
        if w is not None:
            m &= self.spread <= w + 1e-9
        return np.flatnonzero(m)

    def placebo(self, rng: np.random.Generator) -> np.ndarray:
        """Results redrawn with every price right. One draw a window: the four coins rise or fall together as far as their prices allow."""
        u = rng.random(int(self.slot.max()) + 1)[self.slot]
        up_fair = np.where(self.side == 0, self.fair, 1.0 - self.fair)
        up_wins = u < up_fair
        return np.where(self.side == 0, up_wins, ~up_wins).astype(float)


def name(length: str, left: int, sp) -> str:
    coin, side, band, w, cond = sp
    return f"{length}|{left}m left|{coin}|{side}|{100 * band[0]:g}-{100 * band[1]:g}c|spread {'any' if w is None else f'{100 * w:g}c'}|{cond}"


def evaluate(tables: dict, won: dict | None = None, min_trades: int = 30) -> pd.DataFrame:
    rows = []
    for (length, left), t in tables.items():
        w = t.won if won is None else won[(length, left)]
        ret = (w - t.cost) / t.cost
        for sp in t.specs():
            idx = t.trades(sp)
            if len(idx) < min_trades:
                continue
            row = {"rule": name(length, left, sp)}
            for tag, code in (("d", 0), ("v", 1)):
                k = idx[t.split[idx] == code]
                row[f"n_{tag}"] = len(k)
                if len(k) >= 2:
                    mean, z = fx.floored(ret[k], t.cost[k], t.hour[k])
                    row.update({f"ret_{tag}": mean, f"z_{tag}": z, f"cost_{tag}": float(t.cost[k].mean()), f"win_{tag}": float(w[k].mean())})
            rows.append(row)
    res = pd.DataFrame(rows)
    if "z_d" in res:
        res["z_event_d"] = res["z_d"]                     # the name the shared screen looks for
    return res


def load_tables() -> tuple[dict, int]:
    f = pd.read_parquet(CACHE / "crypto_updown.parquet")
    tables = {(length, left): UpDown(g.reset_index(drop=True)) for (length, left), g in f.groupby(["length", "left"])}
    return tables, sum(len(t.specs()) for t in tables.values())


def cmd_run(args: argparse.Namespace) -> None:
    tables, n_rules = load_tables()
    res = evaluate(tables)
    res["candidate"] = fx.screen(res)
    cand = res.loc[res["candidate"], "rule"].tolist()
    log(f"{n_rules:,} rules; {len(res):,} with 30 purchases or more; {len(cand):,} candidates")
    rng = np.random.default_rng(20261111)
    thr, maxima = float("inf"), np.array([])
    if cand:
        by_name = {name(length, left, sp): ((length, left), sp) for (length, left), t in tables.items() for sp in t.specs()}
        picks = [(by_name[c][0], tables[by_name[c][0]].trades(by_name[c][1])) for c in cand]
        maxima = np.full(args.worlds, np.nan)
        for b in range(args.worlds):
            won = {key: t.placebo(rng) for key, t in tables.items()}
            best = -np.inf
            for key, idx in picks:
                t = tables[key]
                k = idx[t.split[idx] == 1]
                if len(k) >= 2:
                    z = fx.floored((won[key][k] - t.cost[k]) / t.cost[k], t.cost[k], t.hour[k])[1]
                    best = max(best, z) if np.isfinite(z) else best
            maxima[b] = best if np.isfinite(best) else np.nan
        thr = float(np.nanquantile(maxima, 0.95))
    res["survivor"] = res["candidate"] & (res.get("n_v", 0) >= 100) & (res.get("z_v", -np.inf) >= thr)
    OUT.mkdir(parents=True, exist_ok=True)
    res.to_parquet(OUT / "ud_all_rules.parquet", index=False)
    counts = []
    for i in range(args.placebo):
        pl = evaluate(tables, won={key: t.placebo(rng) for key, t in tables.items()})
        c = fx.screen(pl)
        counts.append((int(c.sum()), int((c & (pl.get("n_v", 0) >= 100) & (pl.get("z_v", -np.inf) >= thr)).sum())))
        log(f"placebo funnel {i + 1}/{args.placebo}: {counts[-1][0]} candidates, {counts[-1][1]} past the threshold")
    lines = ["Up-or-down crypto markets on Polymarket US: one side bought at its asking price with M minutes of the window left (docs/11, section 7)",
             f"rules in the grid: {n_rules:,}; with 30 purchases or more: {len(res):,}; with 150 or more in discovery: {int((res['n_d'] >= 150).sum()):,}",
             f"best discovery z of any rule with 150 purchases or more: {res.loc[res['n_d'] >= 150, 'z_d'].max():.2f}; "
             f"rules there with a return after the fee above zero: {int(((res['n_d'] >= 150) & (res['ret_d'] > 0)).sum()):,}",
             f"candidates (before 3 November: 150+ purchases, +0.5% or more, z >= 3 by hour): {len(cand):,}",
             (f"threshold: the best validation z among those candidates in 95% of {args.worlds} placebo worlds is below {thr:.2f}"
              f" (median best {np.nanmedian(maxima):.2f}, largest {np.nanmax(maxima):.2f})" if len(maxima)
              else "threshold: not needed, there is no candidate to judge"),
             f"survivors (3 to 10 November: 100+ purchases and z by hour at or above the threshold): {int(res['survivor'].sum()):,}"]
    if counts:
        c = np.array(counts)
        lines.append(f"whole funnel in {len(c)} worlds where every price is right: candidates mean {c[:, 0].mean():.1f} (max {c[:, 0].max()}), "
                     f"past the threshold mean {c[:, 1].mean():.2f} (max {c[:, 1].max()})")
        pd.DataFrame(c, columns=["candidates", "past_threshold"]).to_csv(OUT / "ud_placebo.csv", index=False)
    cols = ["rule", "n_d", "cost_d", "win_d", "ret_d", "z_d", "n_v", "cost_v", "win_v", "ret_v", "z_v", "survivor"]
    show = (res[res["candidate"]] if cand else res[res["n_d"] >= 150]).sort_values("z_d", ascending=False)[[c for c in cols if c in res]].head(40)
    show.to_csv(OUT / "ud_candidates.csv" if cand else OUT / "ud_best_in_discovery.csv", index=False)
    out = show.copy()
    for c in ("ret_d", "ret_v"):
        if c in out:
            out[c] = 100 * out[c]
    head = "candidates, best discovery z first" if cand else "no candidate; for the record, the rules with the best discovery z (150 purchases or more)"
    (OUT / "crypto_updown_output.txt").write_text("\n".join(lines) + f"\n\n{head}\n" + out.round(3).to_string(index=False) + "\n")
    print("\n".join(lines))
    print(out.round(3).to_string(index=False))


def cmd_table(args: argparse.Namespace) -> None:
    """The plain table section 7 promises: asking price against how often that side won, by length and minutes left."""
    f = pd.read_parquet(CACHE / "crypto_updown.parquet")
    f["cost"] = f["ask"] + THETA * f["ask"] * (1.0 - f["ask"])
    rows = []
    for (length, left), g in f.groupby(["length", "left"]):
        for lo, hi in fx.BANDS[:11]:                       # the eleven bands that do not overlap
            a = g[(g["ask"] > lo) & (g["ask"] <= hi)]
            row = {"length": length, "left": left, "band": f"{100 * lo:g}-{100 * hi:g}c", "quotes": len(a)}
            if len(a) >= 2:
                ret = ((a["won"] - a["cost"]) / a["cost"]).to_numpy()
                mean, z = fx.floored(ret, a["cost"].to_numpy(), a["hour"].to_numpy())
                row.update({"ask": a["ask"].mean(), "fair": a["fair"].mean(), "won": a["won"].mean(), "cost": a["cost"].mean(), "ret_pct": 100 * mean, "z_hour": z})
            rows.append(row)
    t = pd.DataFrame(rows)
    t["length"] = pd.Categorical(t["length"], ["5m", "15m", "1h"])
    t = t.sort_values(["length", "left", "band"], ascending=[True, False, True], kind="stable")
    t.to_csv(OUT / "ud_calibration.csv", index=False)
    with open(OUT / "crypto_updown_output.txt", "a") as fh:
        fh.write("\nasking price against how often that side won, by length of market and minutes left (both sides pooled)\n" + t.round(4).to_string(index=False) + "\n")
    print(t.round(4).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("paths")
    p.add_argument("--shard", default=None)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--rate", type=float, default=8.0, help="requests a second")
    p.add_argument("--check", type=int, default=0, help="only compare this many names with their definitions")
    p.set_defaults(fn=cmd_paths)
    sub.add_parser("build").set_defaults(fn=cmd_build)
    p = sub.add_parser("run")
    p.add_argument("--placebo", type=int, default=0)
    p.add_argument("--worlds", type=int, default=500)
    p.set_defaults(fn=cmd_run)
    sub.add_parser("table").set_defaults(fn=cmd_table)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

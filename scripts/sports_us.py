"""Sports on Polymarket US: the search of docs/06_polymarket_us.md, section 9.

    python scripts/sports_us.py quotes [--shard i/n]   # pre-game quotes of every settled moneyline -> data/us_sports/quotes/
    python scripts/sports_us.py build                  # the decision table -> data/cache/sports_us.parquet
    python scripts/sports_us.py run [--placebo 20]     # the grid and the judge -> reports/research/sp_*

A game's market is read three times before its recorded start: 180, 60 and 5
minutes ahead. A rule looks at the quote 60 minutes ahead, may condition on
how the price moved over the two hours before that, and buys at the quote 5
minutes ahead if it is still in the rule's band. Everything is public data.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
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
SP = ROOT / "data" / "us_sports"
OUT = ROOT / "reports" / "research"
CACHE = ROOT / "data" / "cache"
LEADS = (180, 60, 5)                 # minutes before the recorded start
STALE = 30 * 60                      # a quote older than this at its lead time is not used
SPLIT = pd.Timestamp("2026-09-01").timestamp()
LAST = pd.Timestamp("2026-11-11").timestamp()
THETA = 0.095

FAMILIES = ("all", "tennis tour", "tennis lower", "table tennis", "esports", "US leagues", "other")
LEAGUES = {
    "tennis tour": {"atp", "wta", "atpdb", "wtadb", "atpcq", "wtacq"},
    "tennis lower": {"itfme", "itfwo", "itfm", "itfw", "utr"},
    "esports": {"cs2", "lol", "dota2", "valorant", "r6", "ow", "cod", "rl"},
    "US leagues": {"nba", "mlb", "nhl", "nfl", "cfb", "cbb", "wnba", "wcbb"},
}
SPREADS = (0.01, 0.03, None)         # None: any real book (up to 20c)
CONDITIONS = ("none", "quiet", "rose", "fell")
SIDES = ("first", "second")          # the first-named side is the market's "Yes"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def family(sports_type: pd.Series, league: pd.Series) -> np.ndarray:
    out = np.full(len(league), "other", dtype=object)
    for name, leagues in LEAGUES.items():
        out[league.isin(leagues).to_numpy()] = name
    out[(sports_type == "table_tennis_match_winner").to_numpy()] = "table tennis"
    return out


def moneylines() -> pd.DataFrame:
    m = pd.read_parquet(SP / "markets_sports.parquet")
    m = m[(m["market_type"] == "moneyline") & m["game_start_ts"].notna() & m["yes_settle"].notna() & (m["game_start_ts"] < LAST)].copy()
    m["league"] = m["slug"].str.split("-").str[1]
    m["family"] = family(m["sports_type"], m["league"])
    return m


# ------------------------------------------------------------------ quotes
def cmd_quotes(args: argparse.Namespace) -> None:
    pm = PolymarketUS()
    m = moneylines().sort_values("market_id")
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        m = m.iloc[i::n]
    dest = SP / "quotes"
    dest.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    for p in dest.glob("*.parquet"):
        done |= set(pd.read_parquet(p, columns=["slug"])["slug"])
    todo = m[~m["slug"].isin(done)]
    log(f"quotes: {len(m):,} moneylines, {len(todo):,} to fetch")

    def one(r) -> dict | None:
        gs = int(r.game_start_ts)
        try:
            pts = pm.price_history_window(r.slug, gs - (LEADS[0] + 30) * 60, gs + 60)
        except Exception:
            return None                                   # retried on the next run
        row: dict = {"slug": r.slug, "n": len(pts)}
        a = np.array(pts, dtype=float) if pts else np.zeros((0, 3))
        for lead in LEADS:
            k = a[a[:, 0] <= gs - lead * 60]
            ok = len(k) and (gs - lead * 60 - k[-1, 0]) <= STALE
            row[f"age{lead}"] = float(gs - lead * 60 - k[-1, 0]) if ok else np.nan
            row[f"yes{lead}"] = float(k[-1, 1]) if ok else np.nan
            row[f"no{lead}"] = float(k[-1, 2]) if ok else np.nan
        return row

    buf: list[dict] = []
    part, t0, n = 0, time.time(), 0
    tag = (args.shard or "0/1").replace("/", "of")
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(one, list(todo.itertuples())):
            n += 1
            if row is not None:
                buf.append(row)
            if len(buf) >= 10_000:
                pd.DataFrame(buf).to_parquet(dest / f"q_{tag}_{int(time.time())}_{part}.parquet", index=False)
                part, buf = part + 1, []
            if n % 5000 == 0:
                rate = n / (time.time() - t0)
                log(f"quotes: {n:,}/{len(todo):,} ({rate:.1f}/s, eta {(len(todo) - n) / rate / 60:.0f} min)")
    if buf:
        pd.DataFrame(buf).to_parquet(dest / f"q_{tag}_{int(time.time())}_{part}.parquet", index=False)
    log(f"quotes: finished {n:,} in {time.time() - t0:.0f}s")


# ------------------------------------------------------------------- table
def real(yes: pd.Series, no: pd.Series, tick: np.ndarray) -> pd.Series:
    """The filter of docs/06, section 7: a book with real prices on both sides."""
    spread = yes + no - 1.0
    return (yes >= 0.015) & (yes <= 0.985) & (no >= 0.015) & (no <= 0.985) & (spread >= tick - 1e-9) & (spread <= 0.20)


def cmd_build(args: argparse.Namespace) -> None:
    m = moneylines()
    q = pd.concat([pd.read_parquet(p) for p in sorted((SP / "quotes").glob("*.parquet"))], ignore_index=True).drop_duplicates("slug")
    t = m.merge(q, on="slug")
    tick = t["tick"].fillna(0.01).to_numpy()
    ok60, ok5, ok180 = real(t["yes60"], t["no60"], tick), real(t["yes5"], t["no5"], tick), real(t["yes180"], t["no180"], tick)
    log(f"moneylines: {len(m):,}; with quotes fetched: {len(t):,}; a real book 60 minutes ahead: {int(ok60.sum()):,}; and 5 minutes ahead: {int((ok60 & ok5).sum()):,}; "
        f"and 180 minutes ahead: {int((ok60 & ok5 & ok180).sum()):,}")
    jump = (t["yes5"] - t["yes60"]).abs() >= 0.30
    print("share of markets whose price moved 30c or more between 60 and 5 minutes ahead (a recorded start that is too late would show here):")
    print((jump[ok60 & ok5].groupby(t.loc[ok60 & ok5, "family"]).mean() * 100).round(2).to_string())
    t = t[ok60].copy()
    mid60 = (t["yes60"] + 1.0 - t["no60"]) / 2.0
    mid180 = ((t["yes180"] + 1.0 - t["no180"]) / 2.0).where(ok180[ok60])
    move = mid60 - mid180                                   # how "Yes" moved over the two hours before the signal
    ok5 = ok5[ok60]
    parts = []
    for side, ask, nxt, fair, won, mv in ((0, t["yes60"], t["yes5"].where(ok5), mid60, t["yes_settle"], move),
                                          (1, t["no60"], t["no5"].where(ok5), 1.0 - mid60, 1.0 - t["yes_settle"], -move)):
        parts.append(pd.DataFrame({
            "market_id": t["market_id"].to_numpy(), "side": side, "ask": ask.to_numpy(), "next_ask": nxt.to_numpy(),
            "spread": (t["yes60"] + t["no60"] - 1.0).to_numpy(), "family": t["family"].to_numpy(), "league": t["league"].to_numpy(),
            "fair": fair.to_numpy(), "won": won.to_numpy(), "quiet": (mv.abs() < 0.01 - 1e-9).to_numpy(), "rose": (mv >= 0.03 - 1e-9).to_numpy(),
            "fell": (mv <= -0.03 + 1e-9).to_numpy(), "day": np.floor(t["game_start_ts"].to_numpy() / 86_400),
            "split": np.where(t["game_start_ts"].to_numpy() < SPLIT, 0, 1)}))
    f = pd.concat(parts, ignore_index=True)
    f.to_parquet(CACHE / "sports_us.parquet", index=False)
    log(f"table: {len(f):,} rows, {f['market_id'].nunique():,} games; before 1 September {int((f['split'] == 0).sum() / 2):,}, from then {int((f['split'] == 1).sum() / 2):,}")
    print(f.groupby(["family", "split"])["market_id"].nunique().unstack(fill_value=0).to_string())


# --------------------------------------------------------------------- run
class Sports:
    """The table as arrays, and the rules of section 9 evaluated on it."""

    def __init__(self, f: pd.DataFrame):
        self.n = len(f)
        self.market = f["market_id"].to_numpy()
        self.side = f["side"].to_numpy()
        self.ask = f["ask"].to_numpy(dtype=float)
        self.next_ask = f["next_ask"].to_numpy(dtype=float)
        self.cost = self.next_ask + THETA * self.next_ask * (1.0 - self.next_ask)
        self.spread = f["spread"].to_numpy(dtype=float)
        self.won = f["won"].to_numpy(dtype=float)
        self.fair = f["fair"].to_numpy(dtype=float)
        self.day = f["day"].to_numpy()
        self.split = f["split"].to_numpy()
        fam = f["family"].to_numpy()
        self.m_family = {k: (np.ones(self.n, bool) if k == "all" else fam == k) for k in FAMILIES}
        self.m_side = {"first": self.side == 0, "second": self.side == 1}
        self.m_cond = {"none": np.ones(self.n, bool), "quiet": f["quiet"].to_numpy(bool), "rose": f["rose"].to_numpy(bool), "fell": f["fell"].to_numpy(bool)}
        ok = np.isfinite(self.next_ask) & np.isfinite(self.won)
        self.m_band = {b: ok & (self.ask > b[0]) & (self.ask <= b[1]) & (self.next_ask > b[0]) & (self.next_ask <= b[1] + fx.ENTRY_SLACK) for b in fx.BANDS}

    def specs(self):
        return list(product(FAMILIES, SIDES, fx.BANDS, SPREADS, CONDITIONS))

    @staticmethod
    def name(sp) -> str:
        fam, side, band, w, cond = sp
        return f"{fam}|{side}|{100 * band[0]:g}-{100 * band[1]:g}c|spread {'any' if w is None else f'{100 * w:g}c'}|{cond}"

    def trades(self, sp) -> np.ndarray:
        fam, side, band, w, cond = sp
        m = self.m_family[fam] & self.m_side[side] & self.m_band[band] & self.m_cond[cond]
        if w is not None:
            m &= self.spread <= w + 1e-9
        return np.flatnonzero(m)

    def placebo(self, rng: np.random.Generator) -> np.ndarray:
        """Results redrawn with every price right: one draw a game, so its two sides cannot both win."""
        _, inv = np.unique(self.market, return_inverse=True)
        u = rng.random(int(inv.max()) + 1)[inv]
        yes_fair = np.where(self.side == 0, self.fair, 1.0 - self.fair)
        yes_wins = u < yes_fair
        return np.where(self.side == 0, yes_wins, ~yes_wins).astype(float)

    def run(self, won: np.ndarray | None = None, min_trades: int = 30) -> pd.DataFrame:
        won = self.won if won is None else won
        ret = (won - self.cost) / self.cost
        rows = []
        for sp in self.specs():
            idx = self.trades(sp)
            if len(idx) < min_trades:
                continue
            row = {"rule": self.name(sp)}
            for tag, code in (("d", 0), ("v", 1)):
                k = idx[self.split[idx] == code]
                row[f"n_{tag}"] = len(k)
                if len(k) >= 2:
                    mean, z_ev = fx.floored(ret[k], self.cost[k], self.market[k])
                    _, z_day = fx.floored(ret[k], self.cost[k], self.day[k])
                    row.update({f"ret_{tag}": mean, f"z_event_{tag}": z_ev, f"z_week_{tag}": z_day, f"cost_{tag}": float(self.cost[k].mean()),
                                f"win_{tag}": float(won[k].mean())})
            rows.append(row)
        return pd.DataFrame(rows)

    def threshold(self, rows: list[np.ndarray], worlds: int, rng: np.random.Generator) -> tuple[float, np.ndarray]:
        maxima = np.full(worlds, np.nan)
        for b in range(worlds):
            won = self.placebo(rng)
            best = -np.inf
            for idx in rows:
                k = idx[self.split[idx] == 1]
                if len(k) >= 2:
                    z = fx.floored((won[k] - self.cost[k]) / self.cost[k], self.cost[k], self.day[k])[1]
                    best = max(best, z) if np.isfinite(z) else best
            maxima[b] = best if np.isfinite(best) else np.nan
        return float(np.nanquantile(maxima, 0.95)), maxima


def cmd_run(args: argparse.Namespace) -> None:
    t = Sports(pd.read_parquet(CACHE / "sports_us.parquet"))
    specs = t.specs()
    by_name = {t.name(sp): sp for sp in specs}
    res = t.run()
    res["candidate"] = fx.screen(res)
    cand = res.loc[res["candidate"], "rule"].tolist()
    log(f"{len(specs):,} rules; {len(res):,} with 30 trades or more; {len(cand):,} candidates")
    rng = np.random.default_rng(20261111)
    rows = [t.trades(by_name[n]) for n in cand]
    thr, maxima = (float("inf"), np.array([])) if not rows else t.threshold(rows, args.worlds, rng)
    res["survivor"] = res["candidate"] & (res.get("n_v", 0) >= 100) & (res.get("z_week_v", -np.inf) >= thr)
    res.to_parquet(OUT / "sp_all_rules.parquet", index=False)
    counts = []
    for i in range(args.placebo):
        pl = t.run(won=t.placebo(rng))
        c = fx.screen(pl)
        counts.append((int(c.sum()), int((c & (pl.get("n_v", 0) >= 100) & (pl.get("z_week_v", -np.inf) >= thr)).sum())))
        log(f"placebo funnel {i + 1}/{args.placebo}: {counts[-1][0]} candidates, {counts[-1][1]} past the threshold")
    lines = ["Sports on Polymarket US: settled moneylines, bought 5 minutes before the recorded start on a signal 60 minutes before",
             f"rules in the grid: {len(specs):,}; with 30 trades or more: {len(res):,}",
             f"candidates (before 1 September: 150+ trades, +0.5% or more, z >= 3 by game): {len(cand):,}",
             f"threshold: the best validation z among those candidates in 95% of {args.worlds} placebo worlds is below {thr:.2f}"
             + (f" (median best {np.nanmedian(maxima):.2f}, largest {np.nanmax(maxima):.2f})" if len(maxima) else ""),
             f"survivors (from 1 September: 100+ trades and z by day at or above the threshold): {int(res['survivor'].sum()):,}"]
    if counts:
        c = np.array(counts)
        lines.append(f"whole funnel in {len(c)} worlds where every price is right: candidates mean {c[:, 0].mean():.1f} (max {c[:, 0].max()}), "
                     f"past the threshold mean {c[:, 1].mean():.2f} (max {c[:, 1].max()})")
        pd.DataFrame(c, columns=["candidates", "past_threshold"]).to_csv(OUT / "sp_placebo.csv", index=False)
    cols = ["rule", "n_d", "cost_d", "win_d", "ret_d", "z_event_d", "n_v", "cost_v", "win_v", "ret_v", "z_week_v", "survivor"]
    show = res[res["candidate"]].sort_values("z_week_v", ascending=False)[[c for c in cols if c in res]]
    show.to_csv(OUT / "sp_candidates.csv", index=False)
    out = show.copy()
    for c in ("ret_d", "ret_v"):
        if c in out:
            out[c] = 100 * out[c]
    (OUT / "sports_us_output.txt").write_text("\n".join(lines) + "\n\ncandidates, best validation z first\n" + out.round(3).to_string(index=False) + "\n")
    print("\n".join(lines))
    print(out.head(50).round(3).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("quotes")
    p.add_argument("--shard", default=None)
    p.add_argument("--workers", type=int, default=8)
    p.set_defaults(fn=cmd_quotes)
    sub.add_parser("build").set_defaults(fn=cmd_build)
    p = sub.add_parser("run")
    p.add_argument("--placebo", type=int, default=0)
    p.add_argument("--worlds", type=int, default=500)
    p.set_defaults(fn=cmd_run)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

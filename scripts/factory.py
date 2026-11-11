"""The wide search of docs/06_polymarket_us.md: build the tables, run the grid, apply the judge.

    python scripts/factory.py build-intl          # polymarket.com news markets, 5,000 shares or more at the time
    python scripts/factory.py run-intl [--placebo 20]
    python scripts/factory.py build-us            # Polymarket US settled markets (needs scripts/download_us.py first)
    python scripts/factory.py run-us [--placebo 20]

Everything about which rules exist is in src/kht/research/factory.py, and
everything about how one is judged is in docs/06, section 4, fixed before
this ran.
"""

from __future__ import annotations

import argparse
import gc
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import at_the_time as att  # noqa: E402

from kht.backtest.harvest import prepare  # noqa: E402
from kht.research import factory as fx  # noqa: E402
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
pd.set_option("display.max_colwidth", 90)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
CACHE = ROOT / "data" / "cache"
MIN_CUM = 5_000
INTL_SPLIT = pd.Timestamp("2026-01-01").timestamp()         # scheduled end before this: discovery; from it: validation
INTL_LAST = pd.Timestamp("2026-10-27").timestamp()          # later scheduled ends are in the data only if they closed early
US_SPLIT = pd.Timestamp("2026-09-16").timestamp()
US_LAST = pd.Timestamp("2026-11-11").timestamp()
CATEGORY = {"politics": "politics", "geopolitics": "geopolitics", "culture": "culture", "economics": "economy", "finance": "economy",
            "macro": "economy", "tech": "tech", "technology": "tech", "weather": "weather", "climate": "weather"}
PIECES = {"big": ((5_000, 20_000), (20_000, 100_000), (100_000, att.TOP)), "thin": ((5_000, 20_000), (20_000, 100_000)), "thinner": ((5_000, 20_000),)}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def per_series(series: np.ndarray):
    change = np.flatnonzero(np.diff(series)) + 1
    return zip(np.concatenate(([0], change)), np.concatenate((change, [len(series)])))


def conditions(series: np.ndarray, period: np.ndarray, hi: np.ndarray, lo: np.ndarray, last: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """quiet: traded within 3c over the last 7 days in a series older than that.
    rose / fell: the last price is 5c or more above / below what it was 3 to 10 days earlier."""
    n = len(series)
    quiet, rose, fell = np.zeros(n, bool), np.zeros(n, bool), np.zeros(n, bool)
    for a, b in per_series(series):
        per, h, l, x = period[a:b], hi[a:b], lo[a:b], last[a:b]
        start = np.searchsorted(per, per - 6, side="left")
        seasoned = per[0] <= per - 6
        ref = np.searchsorted(per, per - 3, side="right") - 1
        for i in range(b - a):
            j = start[i]
            if seasoned[i]:
                rng = np.nanmax(h[j:i + 1]) - np.nanmin(l[j:i + 1])
                quiet[a + i] = rng <= 0.03 + 1e-9
            k = ref[i]
            if k >= 0 and per[k] >= per[i] - 10 and np.isfinite(x[k]) and np.isfinite(x[i]):
                d = x[i] - x[k]
                rose[a + i] = d >= 0.05 - 1e-9
                fell[a + i] = d <= -0.05 + 1e-9
    return quiet, rose, fell


def next_observation(series: np.ndarray, period: np.ndarray, px: np.ndarray, max_wait: float) -> tuple[np.ndarray, np.ndarray]:
    """For every row: the first later row of its series with a price, if it comes within ``max_wait`` periods."""
    n = len(series)
    pos = np.where(np.isfinite(px), np.arange(n), n)
    later = np.minimum.accumulate(np.append(pos[1:], n)[::-1])[::-1]
    ok = later < n
    j = np.where(ok, later, 0)
    ok &= (series[j] == series) & (period[j] - period <= max_wait)
    return np.where(ok, px[j], np.nan), np.where(ok, period[j], np.nan)


def intl_frame(p: pd.DataFrame, meta: pd.DataFrame, name: str) -> pd.DataFrame:
    """A polymarket.com by-side daily panel (already passed through ``prepare``) as rows of the decision table."""
    m = meta.set_index("market_id")
    yn = (m["outcome0"].str.strip().str.lower() == "yes") & (m["outcome1"].str.strip().str.lower() == "no")
    series = p["series"].to_numpy()
    period = p["period"].to_numpy()
    hi = np.fmax(p["ask_hi"].to_numpy(), p["bid_hi"].to_numpy())
    lo = np.fmin(p["ask_lo"].to_numpy(), p["bid_lo"].to_numpy())
    quiet, rose, fell = conditions(series, period, hi, lo, p["last"].to_numpy())
    next_ask, next_period = next_observation(series, period, p["ask_first"].to_numpy(), 3)
    end = p["end_ts"].to_numpy()
    split = np.where(~np.isfinite(end) | (end > INTL_LAST), -1, np.where(end < INTL_SPLIT, 0, 1))
    return pd.DataFrame({
        "market_id": p["market_id"].to_numpy(), "side": p["side"].to_numpy(), "period": period,
        "ask": p["ask"].to_numpy(), "spread": (p["ask"] - p["bid"]).to_numpy(), "dte": p["days_to_end"].to_numpy(),
        "category": p["category"].map(CATEGORY).fillna("other").to_numpy(),
        "leg": p["neg_risk"].fillna(False).to_numpy(dtype=bool), "yes_no": yn.reindex(p["market_id"]).fillna(False).to_numpy(dtype=bool),
        "quiet": quiet, "rose": rose, "fell": fell, "next_ask": next_ask, "next_period": next_period,
        "fee_theta": p["fee_rate"].to_numpy(), "won": p["won"].to_numpy(), "fair": p["last"].to_numpy(),
        "cluster": p["cluster"].to_numpy(), "split": split, "set": name})


def build_intl(args: argparse.Namespace) -> None:
    frames = []
    for name, ranges in PIECES.items():
        meta = att.news_meta(name)
        tr = pd.concat([att._part(name, [r])[r] for r in ranges], ignore_index=True).sort_values(["market_id", "ts"], kind="stable").reset_index(drop=True)
        log(f"{name}: {len(tr):,} trades in {tr['market_id'].nunique():,} markets from {MIN_CUM:,} shares on")
        p = prepare(add_taker_buy_pnl(by_side(period_quotes(tr, min_cum=MIN_CUM), meta)))
        del tr
        gc.collect()
        frames.append(intl_frame(p, meta, name))
        log(f"{name}: {len(p):,} outcome-days")
        del p
        gc.collect()
    table = pd.concat(frames, ignore_index=True)
    table.to_parquet(CACHE / "factory_intl.parquet", index=False)
    log(f"polymarket.com table: {len(table):,} rows, {table['market_id'].nunique():,} markets; "
        f"discovery {int((table['split'] == 0).sum()):,} rows, validation {int((table['split'] == 1).sum()):,}, unused {int((table['split'] < 0).sum()):,}")


def run(table_path: Path, tag: str, title: str, args: argparse.Namespace) -> None:
    t = fx.Table(pd.read_parquet(table_path))
    specs = list(fx.grid())
    by_name = {sp.name: sp for sp in specs}
    log(f"{title}: {t.n:,} rows; grid of {len(specs):,} rules")
    t0 = time.time()
    res = t.run(specs)
    res["candidate"] = fx.screen(res)
    cand_names = res.loc[res["candidate"], "rule"].tolist()
    log(f"ran in {time.time() - t0:.0f}s: {len(res):,} rules with 30 trades or more, {len(cand_names):,} candidates")
    rng = np.random.default_rng(20261111)
    rows = [t.trades(by_name[n]) for n in cand_names]
    thr, maxima = (float("inf"), np.array([])) if not rows else fx.family_threshold(t, rows, args.worlds, rng)
    res["survivor"] = res["candidate"] & (res.get("n_v", 0) >= 100) & (res.get("z_week_v", -np.inf) >= thr)
    log(f"family threshold from {args.worlds} placebo validation worlds: z >= {thr:.2f}; survivors: {int(res['survivor'].sum()):,}")
    res.to_parquet(OUT / f"f_{tag}_all_rules.parquet", index=False)
    # the whole funnel in worlds with no edge: how many rules does it let through?
    counts = []
    for i in range(args.placebo):
        pl = t.run(specs, won=t.placebo_outcomes(rng))
        c = fx.screen(pl)
        passed = c & (pl.get("n_v", 0) >= 100) & (pl.get("z_week_v", -np.inf) >= thr)
        counts.append((int(c.sum()), int(passed.sum())))
        log(f"placebo funnel {i + 1}/{args.placebo}: {counts[-1][0]} candidates, {counts[-1][1]} past the threshold")
    lines = [title, f"rules in the grid: {len(specs):,}; with 30 trades or more: {len(res):,}",
             f"candidates (discovery: 150+ trades, +0.5% or more, z >= 3 by event): {len(cand_names):,}",
             f"threshold: the best validation z among those candidates in 95% of {args.worlds} placebo worlds is below {thr:.2f}"
             + (f" (median best {np.nanmedian(maxima):.2f}, largest {np.nanmax(maxima):.2f})" if len(maxima) else ""),
             f"survivors (validation: 100+ trades and z by week at or above the threshold): {int(res['survivor'].sum()):,}",
             "z: the variance of a rule's mean return is never taken below what the prices it paid imply"]
    if counts:
        c = np.array(counts)
        lines.append(f"whole funnel in {len(c)} worlds where every price is right: candidates mean {c[:, 0].mean():.1f} (max {c[:, 0].max()}), "
                     f"past the threshold mean {c[:, 1].mean():.2f} (max {c[:, 1].max()}; worlds with any: {int((c[:, 1] > 0).sum())} of {len(c)})")
        pd.DataFrame(c, columns=["candidates", "past_threshold"]).to_csv(OUT / f"f_{tag}_placebo.csv", index=False)
    cols = ["rule", "n_d", "cost_d", "ret_d", "z_event_d", "lost_d", "n_v", "cost_v", "ret_v", "z_week_v", "lost_v", "survivor"]
    cand = res[res["candidate"]].sort_values("z_week_v", ascending=False)
    cand[cols].to_csv(OUT / f"f_{tag}_candidates.csv", index=False)
    surv = cand[cand["survivor"]]
    surv[cols].to_csv(OUT / f"f_{tag}_survivors.csv", index=False)
    show = cand[cols].copy()
    for c in ("ret_d", "ret_v"):
        show[c] = 100 * show[c]
    with (OUT / f"factory_{tag}_output.txt").open("w") as fh:
        fh.write("\n".join(lines) + "\n\ncandidates, best validation z first (survivors marked)\n" + show.round(2).to_string(index=False) + "\n")
    print("\n".join(lines))
    print(show.head(60).round(2).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build-intl").set_defaults(fn=build_intl)
    p = sub.add_parser("run-intl")
    p.add_argument("--placebo", type=int, default=0, help="whole-funnel runs in worlds with no edge")
    p.add_argument("--worlds", type=int, default=500, help="placebo validation worlds for the family threshold")
    p.set_defaults(fn=lambda a: run(CACHE / "factory_intl.parquet", "intl", "Stage 1: polymarket.com news markets, 5,000 shares or more at the time", a))
    p = sub.add_parser("run-us")
    p.add_argument("--placebo", type=int, default=0)
    p.add_argument("--worlds", type=int, default=500)
    p.set_defaults(fn=lambda a: run(CACHE / "factory_us.parquet", "us", "Stage 2b: Polymarket US settled markets", a))
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

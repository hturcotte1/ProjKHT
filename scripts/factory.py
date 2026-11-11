"""The wide search of docs/06_polymarket_us.md: build the tables, run the grid, apply the judge.

    python scripts/factory.py build-intl          # polymarket.com news markets, 5,000 shares or more at the time
    python scripts/factory.py run-intl [--placebo 20]
    python scripts/factory.py build-us            # Polymarket US settled markets (needs scripts/download_us.py first)
    python scripts/factory.py confirm-us          # stage 2: the stage 1 survivors, unchanged, on Polymarket US
    python scripts/factory.py run-us [--placebo 20]   # stage 2b: the whole grid on Polymarket US alone

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


DEADLINE = (r"^(?:by |before |on or before |prior to )?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? \d{1,2}(?:st|nd|rd|th)?(?:, \d{4})?$"
            r"|^(?:by|before) ")


def us_shape(meta: pd.DataFrame, h: pd.DataFrame) -> pd.Series:
    """What kind of thing each Polymarket US market is, by market id.

    polymarket.com flags markets that are one of several answers of which
    only one can be right. Polymarket US has no such flag, so it is read from
    what can be known without the result:

        single      the only market of its event
        deadline    its title is a date ("By August 31, 2026"): one rung of "will this happen by ...?"
        exclusive   in an event whose "Yes" prices add up to about one: a race, a set of brackets
        collection  in an event whose "Yes" prices clearly do not: separate questions under one heading
        unknown     in an event too thinly quoted to tell

    The first, second and fourth are stand-alone questions in the sense of the
    earlier rounds; the third is a leg; the last is left out of every rule.
    The sum is taken on days when at least half of the event's markets show a
    price, and the event is classed by the median of those days.
    """
    m = meta.set_index("market_id")
    n_event = m.groupby("event_id")["slug"].transform("size").fillna(1)
    title = m["title"].fillna("").str.strip().str.lower()
    ya, na = h["yes_ask"], h["no_ask"]
    yes_ok, no_ok = (ya > 0) & (ya < 1), (na > 0) & (na < 1)
    p = np.where(yes_ok & no_ok, (ya + 1.0 - na) / 2.0, np.where(yes_ok, ya, np.where(no_ok, 1.0 - na, np.nan)))
    d = pd.DataFrame({"event_id": h["event_id"].to_numpy(), "period": h["period"].to_numpy(), "p": p}).dropna()
    day = d.groupby(["event_id", "period"])["p"].agg(["sum", "size"]).reset_index()
    size = m.groupby("event_id")["slug"].size()
    day = day[day["size"] >= np.maximum(2, 0.5 * size.reindex(day["event_id"]).to_numpy())]
    med = day.groupby("event_id")["sum"].median()
    s_event = med.reindex(m["event_id"]).to_numpy()
    shape = np.where(n_event.to_numpy() <= 1, "single",
                     np.where(title.str.match(DEADLINE).to_numpy(), "deadline",
                              np.where((s_event >= 0.8) & (s_event <= 1.2), "exclusive",
                                       np.where((s_event < 0.7) | (s_event > 1.3), "collection", "unknown"))))
    return pd.Series(shape, index=m.index)


def build_us(args: argparse.Namespace) -> None:
    """Polymarket US settled markets as a decision table: one row per outcome per day, from the gateway's daily quotes."""
    us = ROOT / "data" / "us"
    meta_all = pd.concat([pd.read_parquet(p) for p in sorted(us.glob("markets*.parquet"))], ignore_index=True).drop_duplicates("market_id")
    meta = meta_all[meta_all["yes_settle"].notna() & meta_all["end_ts"].notna() & (meta_all["end_ts"] <= US_LAST)]
    h = pd.concat([pd.read_parquet(p) for p in sorted((us / "history").glob("*.parquet"))], ignore_index=True)
    h = h.merge(meta[["slug", "market_id", "event_id"]], on="slug")
    # a point stamped exactly at midnight is the close of the day before
    h["period"] = (h["ts"] - 1) // 86_400
    h = h.sort_values(["market_id", "ts"]).drop_duplicates(["market_id", "period"], keep="last")
    h["shape"] = us_shape(meta_all, h).reindex(h["market_id"]).to_numpy()
    spread = h["yes_ask"] + h["no_ask"] - 1.0
    # An empty side of the book shows up as a default price. Keep a row only when both asks are real
    # prices and the book is not crossed or absurdly wide; rules that accept "any" spread get no more than this.
    real = (h["yes_ask"] > 0) & (h["yes_ask"] < 1) & (h["no_ask"] > 0) & (h["no_ask"] < 1) & (spread >= -1e-9) & (spread <= 0.20)
    log(f"{len(h):,} market-days of quotes in {h['market_id'].nunique():,} settled markets; {int(real.sum()):,} with a real two-sided book")
    h = h[real]
    spread = spread[real]
    m = meta.set_index("market_id")
    shape = h["shape"].to_numpy()
    end = m["end_ts"].reindex(h["market_id"]).to_numpy()
    close_ts = (h["period"].to_numpy() + 1) * 86_400.0
    event = m["event_id"].reindex(h["market_id"]).to_numpy()
    settle = m["yes_settle"].reindex(h["market_id"]).to_numpy()
    cat = m["category"].reindex(h["market_id"]).map(CATEGORY).fillna("other").to_numpy()
    mid = (h["yes_ask"].to_numpy() + 1.0 - h["no_ask"].to_numpy()) / 2.0
    parts = []
    for side, ask, fair, won in ((0, h["yes_ask"].to_numpy(), mid, settle), (1, h["no_ask"].to_numpy(), 1.0 - mid, 1.0 - settle)):
        parts.append(pd.DataFrame({
            "market_id": h["market_id"].to_numpy(), "side": side, "period": h["period"].to_numpy(), "ask": ask, "spread": spread.to_numpy(),
            "dte": (end - close_ts) / 86_400, "category": cat, "leg": shape == "exclusive", "yes_no": shape != "unknown", "shape": shape, "fair": fair,
            "fee_theta": 0.095, "won": won, "cluster": np.where(np.isfinite(event), event, -h["market_id"].to_numpy()),
            "time_cluster": np.floor(end / 86_400), "split": np.where(end < US_SPLIT, 0, 1)}))
    f = pd.concat(parts, ignore_index=True).sort_values(["market_id", "side", "period"], kind="stable").reset_index(drop=True)
    key = f["market_id"].to_numpy().astype(np.int64) * 2 + f["side"].to_numpy()
    series = np.cumsum(np.concatenate(([True], key[1:] != key[:-1]))) - 1
    period = f["period"].to_numpy()
    f["quiet"], f["rose"], f["fell"] = conditions(series, period, f["fair"].to_numpy(), f["fair"].to_numpy(), f["fair"].to_numpy())
    f["next_ask"], f["next_period"] = next_observation(series, period, f["ask"].to_numpy(), 3)
    f.to_parquet(CACHE / "factory_us.parquet", index=False)
    log(f"Polymarket US table: {len(f):,} rows, {f['market_id'].nunique():,} markets, {f['cluster'].nunique():,} events; "
        f"ending before 16 September {int((f['split'] == 0).sum()):,} rows, from then {int((f['split'] == 1).sum()):,}")
    print(f.groupby(["category", "shape"])["market_id"].nunique().unstack(fill_value=0).to_string())


def confirm_us(args: argparse.Namespace) -> None:
    """Stage 2: the stage 1 survivors, unchanged, on every settled Polymarket US market, with the US fee."""
    frame = pd.read_parquet(CACHE / "factory_us.parquet")
    frame["split"] = 1                                   # nothing was searched here: the whole history is the test
    t = fx.Table(frame)
    names = pd.read_csv(OUT / "f_intl_survivors.csv")["rule"].tolist()
    by_name = {sp.name: sp for sp in fx.grid()}
    specs = [by_name[n] for n in names]
    res = t.run(specs, min_trades=1)
    rows = [t.trades(sp) for sp in specs]
    rng = np.random.default_rng(20261111)
    thr, maxima = fx.family_threshold(t, rows, args.worlds, rng)
    res = pd.DataFrame({"rule": names}).merge(res, on="rule", how="left")
    res["n_v"] = res["n_v"].fillna(0).astype(int)
    res["confirmed"] = (res["n_v"] >= 100) & (res["z_week_v"] >= thr)
    cols = ["rule", "n_v", "cost_v", "ret_v", "z_week_v", "lost_v", "confirmed"]
    for c in cols:
        if c not in res:
            res[c] = np.nan
    res[cols].to_csv(OUT / "f_us_confirmation.csv", index=False)
    lines = ["Stage 2: the stage 1 survivors on Polymarket US, every settled market, fee 0.095 x p x (1 - p)",
             f"rules carried over: {len(names)}; with 100 trades or more there: {int((res['n_v'] >= 100).sum())}; with any: {int((res['n_v'] > 0).sum())}",
             f"threshold: the best z among them in 95% of {args.worlds} placebo worlds is below {thr:.2f}",
             f"confirmed (100+ trades and z by day of settlement at or above the threshold): {int(res['confirmed'].sum())}"]
    show = res[cols].copy()
    show["ret_v"] = 100 * show["ret_v"]
    with (OUT / "factory_us_confirmation_output.txt").open("w") as fh:
        fh.write("\n".join(lines) + "\n\n" + show.round(2).to_string(index=False) + "\n")
    print("\n".join(lines))
    print(show.round(2).to_string(index=False))


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
    sub.add_parser("build-us").set_defaults(fn=build_us)
    p = sub.add_parser("confirm-us")
    p.add_argument("--worlds", type=int, default=500)
    p.set_defaults(fn=confirm_us)
    p = sub.add_parser("run-us")
    p.add_argument("--placebo", type=int, default=0)
    p.add_argument("--worlds", type=int, default=500)
    p.set_defaults(fn=lambda a: run(CACHE / "factory_us.parquet", "us", "Stage 2b: Polymarket US settled markets", a))
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

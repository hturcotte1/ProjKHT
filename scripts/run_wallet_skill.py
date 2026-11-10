"""Does a wallet's past trading skill persist? (first look; plan fixed before running)

Every tape row names the taker's wallet. If some wallets are reliably better
informed, their buying would be the cleanest form of the project's thesis: a
shift in perception that can be seen before the price has finished moving.
Nothing at wallet level had been looked at for non-sports markets when this
file was committed.

PLAN, FIXED BEFORE THE FIRST RUN
--------------------------------
Universe: resolved non-sports, non-crypto markets; trades made after the
market had already traded 100,000 shares; prices paid between 5c and 95c.
Each taker trade is read as a bet on the outcome it bought (a taker sale of
one outcome is a purchase of the other at one minus the price).

Skill, walk-forward by calendar quarter. At the start of quarter Q, using
only trades in markets that had *resolved* before Q:
  1. fit the calibration line P(pays) = sigmoid(a + b*logit(price)) on those
     trades, so that buying favourites is not mistaken for skill;
  2. a trade's edge is payoff minus that calibrated probability;
  3. a wallet's score is the t-statistic of its mean edge over its past
     trades, for wallets with at least 50 such trades in at least 10 markets;
  4. wallets are cut into fifths by score.

Test: trades made during Q by ranked wallets, one per wallet, market, outcome
and day (the first), in markets since resolved.
  PRIMARY: a follower buys the same outcome at the next taker-buy print at
  least 60 seconds later and within 24 hours, pays today's taker fee and
  holds to resolution. The top fifth counts as a lead worth a full test only
  if its followers' mean return is positive with |t| >= 3 (clustered by
  event) AND exceeds the bottom fifth's by |t| >= 3.
  Reported alongside: the edge at the wallet's own price, the calibrated
  edge, and all fifths, pooled over quarters and by half of the sample.

A lead here would still need a forward test and a faster engine than the
three-hourly paper trader; it would not change what is deployed.

Usage: python scripts/run_wallet_skill.py [--out reports/research]
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.data.download import DATA_DIR, load_meta
from kht.research.quotes import CURRENT_FEE_RATE
from kht.research.stats import mean_cluster

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
MIN_CUM = 100_000
PX_LO, PX_HI = 0.05, 0.95
MIN_TRADES, MIN_MARKETS = 50, 10
FOLLOW_DELAY, FOLLOW_WINDOW = 60, 86_400
SPLIT_TS = pd.Timestamp("2026-05-01", tz="UTC").timestamp()


def _one_tape(args: tuple[str, int]) -> pd.DataFrame | None:
    condition_id, market_id = args
    path = DATA_DIR / "trades" / f"{condition_id}.parquet"
    if not path.exists():
        return None
    t = pd.read_parquet(path, columns=["timestamp", "side", "outcome_index", "price", "size", "proxy_wallet"])
    if t.empty:
        return None
    idx0 = t["outcome_index"].to_numpy() == 0
    buy = t["side"].to_numpy() == "BUY"
    price = t["price"].to_numpy()
    return pd.DataFrame({
        "market_id": np.int64(market_id),
        "ts": t["timestamp"].to_numpy(dtype=np.int64),
        "p0": np.where(idx0, price, 1.0 - price).astype(np.float32),
        "dir0": np.where(idx0 == buy, 1, -1).astype(np.int8),
        "size": t["size"].to_numpy(dtype=np.float32),
        # a stable 64-bit hash instead of 42-character strings: 60M of those do not fit in memory
        "wallet": pd.util.hash_array(t["proxy_wallet"].to_numpy(dtype=object)).view(np.int64),
    })


def load_trades(meta: pd.DataFrame, workers: int = 4) -> pd.DataFrame:
    have = {p.stem for p in (DATA_DIR / "trades").glob("*.parquet")}
    sel = meta[meta["condition_id"].isin(have)]
    jobs = list(zip(sel["condition_id"], sel["market_id"].astype(int)))
    parts = []
    with cf.ProcessPoolExecutor(max_workers=workers) as pool:
        for part in pool.map(_one_tape, jobs, chunksize=200):
            if part is not None:
                parts.append(part)
    df = pd.concat(parts, ignore_index=True)
    del parts
    df = df.sort_values(["market_id", "ts"], kind="stable").reset_index(drop=True)
    total = meta.set_index("market_id")["volume"].reindex(df["market_id"]).to_numpy()
    size = df["size"].to_numpy(dtype=np.float64)
    rev = pd.Series(size[::-1]).groupby(df["market_id"].to_numpy()[::-1], sort=False).cumsum().to_numpy()[::-1]
    df["cum_before"] = np.maximum(total - rev, 0.0).astype(np.float32)
    return df


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def fit_line(price: np.ndarray, won: np.ndarray, iters: int = 60) -> tuple[float, float]:
    X = np.column_stack([np.ones(len(price)), logit(price)])
    beta = np.array([0.0, 1.0])
    for _ in range(iters):
        mu = 1 / (1 + np.exp(-(X @ beta)))
        w = mu * (1 - mu)
        step = np.linalg.solve(X.T @ (X * w[:, None]) + 1e-9 * np.eye(2), X.T @ (won - mu))
        beta = beta + np.clip(step, -1.0, 1.0)
        if np.abs(step).max() < 1e-10:
            break
    return float(beta[0]), float(beta[1])


def next_print(series: np.ndarray, ts: np.ndarray, px: np.ndarray, q_series: np.ndarray, q_ts: np.ndarray):
    """For each query (series, time): price and time of the first print of that
    series at or after the time. ``series, ts`` must be sorted together."""
    key = series.astype(np.int64) * (1 << 32) + ts
    i = np.searchsorted(key, q_series.astype(np.int64) * (1 << 32) + q_ts, side="left")
    ok = i < len(key)
    i = np.where(ok, i, 0)
    ok &= series[i] == q_series
    return np.where(ok, px[i], np.nan), np.where(ok, ts[i], -1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/research")
    args = ap.parse_args()
    out = Path(args.out)
    t0 = time.time()

    meta = load_meta("closed")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    meta = meta[(~meta["category"].isin(["sports", "crypto"])) & (life >= 2) & resolved].copy()
    tr = load_trades(meta)
    tr = tr[tr["cum_before"] >= MIN_CUM].reset_index(drop=True)
    m = meta.set_index("market_id")
    win = m["winner"].reindex(tr["market_id"]).to_numpy()
    final0 = m["final0"].reindex(tr["market_id"]).to_numpy()
    pay0 = np.where(win == 0, 1.0, np.where(win == 1, 0.0, np.where(final0 == 0.5, 0.5, np.nan)))
    side = (tr["dir0"].to_numpy() < 0).astype(np.int8)                 # outcome bought: 0 or 1
    p0 = tr["p0"].to_numpy(dtype=np.float64)
    tr["side"] = side
    tr["px"] = np.where(side == 0, p0, 1.0 - p0)
    tr["pay"] = np.where(side == 0, pay0, 1.0 - pay0)
    tr["closed_ts"] = m["closed_ts"].reindex(tr["market_id"]).to_numpy()
    ev = m["event_id"].reindex(tr["market_id"]).to_numpy()
    tr["cluster"] = np.where(ev >= 0, ev, -tr["market_id"].to_numpy())
    tr["fee_rate"] = m["category"].reindex(tr["market_id"]).map(CURRENT_FEE_RATE).fillna(0.05).to_numpy()
    tr["end_ts"] = m["end_ts"].reindex(tr["market_id"]).to_numpy()
    tr = tr[np.isfinite(tr["pay"]) & np.isfinite(tr["closed_ts"])].reset_index(drop=True)
    tr["series"] = (tr["market_id"].to_numpy() * 2 + tr["side"].to_numpy()).astype(np.int64)
    print(f"{len(tr):,} trades by {tr['wallet'].nunique():,} wallets in {tr['market_id'].nunique():,} markets "
          f"({time.time() - t0:.0f}s)", flush=True)

    # every print, by outcome and time, for the follower's entry
    o = np.lexsort((tr["ts"].to_numpy(), tr["series"].to_numpy()))
    all_series, all_ts, all_px = tr["series"].to_numpy()[o], tr["ts"].to_numpy()[o], tr["px"].to_numpy()[o]

    mid = tr[(tr["px"] > PX_LO) & (tr["px"] < PX_HI)]
    data_end = float(tr["ts"].max())
    quarters = pd.period_range(pd.Timestamp(tr["ts"].min(), unit="s").to_period("Q") + 2,
                               pd.Timestamp(data_end, unit="s").to_period("Q"), freq="Q")
    tests, wallets_ranked, calib = [], [], []
    for q in quarters:
        q0, q1 = q.start_time.timestamp(), (q + 1).start_time.timestamp()
        past = mid[mid["closed_ts"] < q0]
        if len(past) < 200_000:
            continue
        samp = past.sample(min(len(past), 1_500_000), random_state=1)
        a, b = fit_line(samp["px"].to_numpy(), samp["pay"].to_numpy())
        calib.append({"quarter": str(q), "a": a, "b": b, "past_trades": len(past)})
        edge = past["pay"].to_numpy() - 1 / (1 + np.exp(-(a + b * logit(past["px"].to_numpy()))))
        g = pd.DataFrame({"wallet": past["wallet"].to_numpy(), "e": edge, "e2": edge * edge,
                          "market_id": past["market_id"].to_numpy()}).groupby("wallet", sort=False)
        w = g.agg(n=("e", "size"), s=("e", "sum"), s2=("e2", "sum"), markets=("market_id", "nunique"))
        w = w[(w["n"] >= MIN_TRADES) & (w["markets"] >= MIN_MARKETS)]
        mean = w["s"] / w["n"]
        sd = np.sqrt(np.maximum(w["s2"] / w["n"] - mean ** 2, 1e-12))
        w["score"] = mean / (sd / np.sqrt(w["n"]))
        w["fifth"] = pd.qcut(w["score"], 5, labels=False, duplicates="drop") + 1
        wallets_ranked.append(w.assign(quarter=str(q), past_mean_edge=mean)[["quarter", "n", "markets", "past_mean_edge", "score", "fifth"]])
        fut = mid[(mid["ts"] >= q0) & (mid["ts"] < q1) & mid["wallet"].isin(w.index)].copy()
        fut["fifth"] = w["fifth"].reindex(fut["wallet"]).to_numpy()
        fut["day"] = fut["ts"] // 86_400
        fut = fut.sort_values("ts").drop_duplicates(["wallet", "market_id", "side", "day"], keep="first")
        fut["calibrated"] = 1 / (1 + np.exp(-(a + b * logit(fut["px"].to_numpy()))))
        fut["quarter"] = str(q)
        tests.append(fut)
        print(f"{q}: calibration a={a:+.3f} b={b:.3f}; {len(w):,} ranked wallets; {len(fut):,} test trades "
              f"({time.time() - t0:.0f}s)", flush=True)

    t = pd.concat(tests, ignore_index=True)
    nx_px, nx_ts = next_print(all_series, all_ts, all_px, t["series"].to_numpy(), t["ts"].to_numpy() + FOLLOW_DELAY)
    ok = np.isfinite(nx_px) & (nx_ts - t["ts"].to_numpy() <= FOLLOW_WINDOW) & (nx_ts < t["closed_ts"].to_numpy())
    t["follow_px"] = np.where(ok, nx_px, np.nan)
    t["own_edge"] = t["pay"] - t["px"]
    t["calib_edge"] = t["pay"] - t["calibrated"]
    cost = t["follow_px"] + t["fee_rate"] * t["follow_px"] * (1 - t["follow_px"])
    t["follow_ret"] = (t["pay"] - cost) / cost
    t["holdout"] = t["end_ts"] < SPLIT_TS

    def table(d: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for fifth, g in d.groupby("fifth"):
            f = g[g["follow_px"].notna()]
            a_ = mean_cluster(g["own_edge"].to_numpy(), g["cluster"].to_numpy())
            c_ = mean_cluster(g["calib_edge"].to_numpy(), g["cluster"].to_numpy())
            r_ = mean_cluster(f["follow_ret"].to_numpy(), f["cluster"].to_numpy())
            rows.append({"past-skill fifth": int(fifth), "wallets": int(g["wallet"].nunique()), "trades": len(g),
                         "events": int(g["cluster"].nunique()), "avg price": float(g["px"].mean()),
                         "edge at own price c": 100 * a_.mean, "t own": a_.t,
                         "calibrated edge c": 100 * c_.mean, "t calib": c_.t,
                         "followed": len(f), "avg follow price": float(f["follow_px"].mean()),
                         "follower ret %": 100 * r_.mean, "t follow": r_.t})
        return pd.DataFrame(rows)

    def top_minus_bottom(d: pd.DataFrame) -> str:
        f = d[d["follow_px"].notna() & d["fifth"].isin([1, 5])]
        x = np.where(f["fifth"] == 5, 1.0, 0.0)
        # difference of means with event-clustered errors, via the mean of a signed, re-weighted return
        n1, n0 = x.sum(), (1 - x).sum()
        z = f["follow_ret"].to_numpy() * (x / n1 - (1 - x) / n0) * len(f)
        r = mean_cluster(z, f["cluster"].to_numpy())
        return f"top fifth minus bottom fifth, follower return: {100 * r.mean:+.2f}% (t = {r.t:.2f})"

    res = []
    for name, mask in (("all quarters", np.ones(len(t), bool)), ("scheduled end before May 2026", t["holdout"].to_numpy()),
                       ("scheduled end from May 2026", ~t["holdout"].to_numpy())):
        tb = table(t[mask])
        res.append(tb.assign(sample=name))
        print(f"\n[{name}] trades of ranked wallets in the quarter after ranking\n", tb.round(2).to_string(index=False))
        print(top_minus_bottom(t[mask]))
    pd.concat(res, ignore_index=True).to_csv(out / "w_wallet_skill_fifths.csv", index=False)
    pd.DataFrame(calib).to_csv(out / "w_wallet_calibration_by_quarter.csv", index=False)
    byq = []
    for q, g in t.groupby("quarter"):
        for fifth in (1, 5):
            f = g[(g["fifth"] == fifth) & g["follow_px"].notna()]
            if len(f) >= 30:
                r = mean_cluster(f["follow_ret"].to_numpy(), f["cluster"].to_numpy())
                byq.append({"quarter": q, "fifth": fifth, "followed": len(f), "follower ret %": 100 * r.mean, "t": r.t})
    byq = pd.DataFrame(byq)
    byq.to_csv(out / "w_wallet_skill_by_quarter.csv", index=False)
    print("\nby quarter, bottom and top fifth\n", byq.round(2).to_string(index=False))
    ranked = pd.concat(wallets_ranked)
    print(f"\nranked wallet-quarters: {len(ranked):,}; median past trades {ranked['n'].median():.0f}, markets {ranked['markets'].median():.0f}")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

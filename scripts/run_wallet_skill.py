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
from kht.research.quotes import CURRENT_FEE_RATE, next_print_after
from kht.research.stats import mean_cluster

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
MIN_CUM = 100_000
PX_LO, PX_HI = 0.05, 0.95
MIN_TRADES, MIN_MARKETS = 50, 10
FOLLOW_DELAY, FOLLOW_WINDOW = 60, 86_400
SPLIT_TS = pd.Timestamp("2026-05-01", tz="UTC").timestamp()


def _one_tape(args: tuple[str, int, float]) -> pd.DataFrame | None:
    """One market's trades after it had traded MIN_CUM shares, as bets on an outcome."""
    condition_id, market_id, total_volume = args
    path = DATA_DIR / "trades" / f"{condition_id}.parquet"
    if not path.exists():
        return None
    t = pd.read_parquet(path, columns=["timestamp", "side", "outcome_index", "price", "size", "proxy_wallet"])
    if t.empty:
        return None
    t = t.sort_values("timestamp", kind="stable")
    size = t["size"].to_numpy(dtype=np.float64)
    # shares traded before each row, counted back from the market's total (tapes can be truncated at the start)
    cum_before = np.maximum(total_volume - np.cumsum(size[::-1])[::-1], 0.0)
    keep = cum_before >= MIN_CUM
    if not keep.any():
        return None
    t = t[keep]
    idx0 = t["outcome_index"].to_numpy() == 0
    buy = t["side"].to_numpy() == "BUY"
    price = t["price"].to_numpy()
    side = np.where(idx0 == buy, 0, 1).astype(np.int8)          # the outcome the taker ended up long
    px = np.where(buy, price, 1.0 - price).astype(np.float32)   # what that outcome cost per share
    return pd.DataFrame({
        "market_id": np.int32(market_id),
        "ts": t["timestamp"].to_numpy(dtype=np.int64),
        "side": side,
        "px": px,
        # a stable 64-bit hash instead of 42-character strings: 60M of those do not fit in memory
        "wallet": pd.util.hash_array(t["proxy_wallet"].to_numpy(dtype=object)).view(np.int64),
    })


def load_trades(meta: pd.DataFrame, workers: int = 4) -> pd.DataFrame:
    have = {p.stem for p in (DATA_DIR / "trades").glob("*.parquet")}
    sel = meta[meta["condition_id"].isin(have)]
    jobs = list(zip(sel["condition_id"], sel["market_id"].astype(int), sel["volume"].astype(float)))
    parts = []
    with cf.ProcessPoolExecutor(max_workers=workers) as pool:
        for part in pool.map(_one_tape, jobs, chunksize=200):
            if part is not None:
                parts.append(part)
    return pd.concat(parts, ignore_index=True)


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/research")
    args = ap.parse_args()
    out = Path(args.out)
    t0 = time.time()
    rng = np.random.default_rng(1)

    meta = load_meta("closed")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    meta = meta[(~meta["category"].isin(["sports", "crypto"])) & (life >= 2) & resolved & meta["closed_ts"].notna()].copy()
    m = meta.set_index("market_id")
    tr = load_trades(meta)
    tr = tr.sort_values(["market_id", "side", "ts"], kind="stable").reset_index(drop=True)
    market = tr["market_id"].to_numpy()
    side = tr["side"].to_numpy()
    ts = tr["ts"].to_numpy()
    px = tr["px"].to_numpy(dtype=np.float64)
    win = m["winner"].reindex(market).to_numpy()
    final0 = m["final0"].reindex(market).to_numpy()
    pay0 = np.where(win == 0, 1.0, np.where(win == 1, 0.0, 0.5))
    pay = np.where(side == 0, pay0, 1.0 - pay0)
    closed = m["closed_ts"].reindex(market).to_numpy(dtype=np.float64)
    series = market.astype(np.int64) * 2 + side
    codes, uniq = pd.factorize(tr["wallet"].to_numpy())
    del tr
    print(f"{len(ts):,} trades by {len(uniq):,} wallets in {len(np.unique(market)):,} markets ({time.time() - t0:.0f}s)", flush=True)

    mid = (px > PX_LO) & (px < PX_HI)
    # distinct (wallet, market) pairs among mid-priced trades, for the "at least 10 markets" condition
    pair = pd.DataFrame({"w": codes[mid], "m": market[mid]}).drop_duplicates()
    pair_w = pair["w"].to_numpy()
    pair_closed = m["closed_ts"].reindex(pair["m"]).to_numpy(dtype=np.float64)
    del pair

    quarters = pd.period_range(pd.Timestamp(int(ts.min()), unit="s").to_period("Q") + 2,
                               pd.Timestamp(int(ts.max()), unit="s").to_period("Q"), freq="Q")
    K = len(uniq)
    tests, calib, ranked_n = [], [], []
    for q in quarters:
        q0, q1 = q.start_time.timestamp(), (q + 1).start_time.timestamp()
        past = np.flatnonzero(mid & (closed < q0))
        if len(past) < 200_000:
            continue
        samp = rng.choice(past, size=min(len(past), 1_500_000), replace=False)
        a, b = fit_line(px[samp], pay[samp])
        edge = pay[past] - 1 / (1 + np.exp(-(a + b * logit(px[past]))))
        n = np.bincount(codes[past], minlength=K)
        s1 = np.bincount(codes[past], weights=edge, minlength=K)
        s2 = np.bincount(codes[past], weights=edge * edge, minlength=K)
        n_markets = np.bincount(pair_w[pair_closed < q0], minlength=K)
        ok = (n >= MIN_TRADES) & (n_markets >= MIN_MARKETS)
        mean = s1[ok] / n[ok]
        sd = np.sqrt(np.maximum(s2[ok] / n[ok] - mean ** 2, 1e-12))
        score = mean / (sd / np.sqrt(n[ok]))
        fifth_of = np.zeros(K, dtype=np.int8)                       # 0 = not ranked
        fifth_of[np.flatnonzero(ok)] = pd.qcut(score, 5, labels=False, duplicates="drop") + 1
        fut = np.flatnonzero(mid & (ts >= q0) & (ts < q1) & (fifth_of[codes] > 0))
        f = pd.DataFrame({"i": fut, "wallet": codes[fut], "market_id": market[fut], "side": side[fut],
                          "day": ts[fut] // 86_400, "ts": ts[fut]})
        f = f.sort_values("ts", kind="stable").drop_duplicates(["wallet", "market_id", "side", "day"], keep="first")
        i = f["i"].to_numpy()
        tests.append(pd.DataFrame({
            "quarter": str(q), "wallet": codes[i], "fifth": fifth_of[codes[i]], "market_id": market[i], "side": side[i],
            "ts": ts[i], "px": px[i], "pay": pay[i], "closed_ts": closed[i], "series": series[i],
            "calibrated": 1 / (1 + np.exp(-(a + b * logit(px[i])))),
        }))
        calib.append({"quarter": str(q), "a": a, "b": b, "past_trades": len(past), "ranked_wallets": int(ok.sum()),
                      "test_trades": len(i)})
        ranked_n.append((float(np.median(n[ok])), float(np.median(n_markets[ok]))))
        print(f"{q}: calibration a={a:+.3f} b={b:.3f}; {int(ok.sum()):,} ranked wallets; {len(i):,} test trades "
              f"({time.time() - t0:.0f}s)", flush=True)

    t = pd.concat(tests, ignore_index=True)
    # the follower's price: the next print of the same outcome at least a minute later (prints are sorted by series, ts)
    nx_px, nx_ts = next_print_after(series, ts, px, t["series"].to_numpy(), t["ts"].to_numpy() + FOLLOW_DELAY)
    ok = np.isfinite(nx_px) & (nx_ts - t["ts"].to_numpy() <= FOLLOW_WINDOW) & (nx_ts < t["closed_ts"].to_numpy())
    t["follow_px"] = np.where(ok, nx_px, np.nan)
    ev = m["event_id"].reindex(t["market_id"]).to_numpy()
    t["cluster"] = np.where(ev >= 0, ev, -t["market_id"].to_numpy())
    fee_rate = m["category"].reindex(t["market_id"]).map(CURRENT_FEE_RATE).fillna(0.05).to_numpy()
    t["own_edge"] = t["pay"] - t["px"]
    t["calib_edge"] = t["pay"] - t["calibrated"]
    cost = t["follow_px"] + fee_rate * t["follow_px"] * (1 - t["follow_px"])
    t["follow_ret"] = (t["pay"] - cost) / cost
    t["holdout"] = m["end_ts"].reindex(t["market_id"]).to_numpy() < SPLIT_TS

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
        x = (f["fifth"] == 5).to_numpy(dtype=float)
        n1, n0 = x.sum(), (1 - x).sum()
        if n1 < 30 or n0 < 30:
            return "top fifth minus bottom fifth: too few trades"
        # difference of the two means as the mean of one re-weighted series, so the event clustering carries over
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
    # ---- NOT IN THE PLAN, added after the planned tables were read. The
    # planned return is a ratio, which cheap contracts dominate; in cents per
    # share the picture is easier to read, and the fee is the obvious suspect,
    # so the same followers are split by whether their market charges one.
    t["category"] = m["category"].reindex(t["market_id"]).to_numpy()
    t["follow_edge_c"] = 100 * (t["pay"] - cost)
    t["follow_gross_c"] = 100 * (t["pay"] - t["follow_px"])
    t["slip_c"] = 100 * (t["follow_px"] - t["px"])
    rows = []
    for name, mask in (("all markets", np.ones(len(t), bool)), ("fee-free (geopolitics)", (t["category"] == "geopolitics").to_numpy()),
                       ("markets with a fee", (t["category"] != "geopolitics").to_numpy())):
        for fifth, g in t[mask & t["follow_px"].notna().to_numpy()].groupby("fifth"):
            own = mean_cluster((100 * g["own_edge"]).to_numpy(), g["cluster"].to_numpy())
            net = mean_cluster(g["follow_edge_c"].to_numpy(), g["cluster"].to_numpy())
            rows.append({"markets": name, "past-skill fifth": int(fifth), "followed": len(g), "events": int(g["cluster"].nunique()),
                         "wallet's own edge c": own.mean, "t own": own.t, "price paid later c": float(g["slip_c"].mean()),
                         "fee c": float((g["follow_gross_c"] - g["follow_edge_c"]).mean()),
                         "follower edge c": net.mean, "t follower": net.t})
    extra = pd.DataFrame(rows)
    extra.to_csv(out / "w_wallet_follow_cents_unplanned.csv", index=False)
    print("\nNOT IN THE PLAN: the follower's result in cents per share, by whether the market charges a fee\n",
          extra.round(2).to_string(index=False))

    med = np.median(np.array(ranked_n), axis=0)
    print(f"\na ranked wallet has, at the median quarter, {med[0]:.0f} past trades in {med[1]:.0f} markets")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

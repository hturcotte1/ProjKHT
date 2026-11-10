"""Fit the edge model the live strategy uses, and check it walk-forward.

The model is deliberately tiny: one calibration line for all trades,

    P(pays) = sigmoid(a + b * logit(ask))

(``a = 0, b = 1`` means prices are right; ``b > 1`` means they are compressed
toward 50%), plus one intercept shift per segment. Shifts are shrunk toward
zero in proportion to how little data a segment has, so a segment with 40
trades cannot talk itself into a large edge.

Training rows are R1-style signals (one per market: the first day a side's ask
is in the band with 3-60 scheduled days left), entered at the next taker-buy
print. The walk-forward table answers the only question that matters for a
model like this: when it says the edge is larger, is the realised return larger?

Usage: python scripts/fit_model.py [--out config/model.json] [--report reports/research]
"""

from __future__ import annotations

import argparse
import json
import math
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.backtest.harvest import Rule, candidate_trades, prepare
from kht.data.download import load_meta
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes
from kht.research.sports import build_trades_table
from kht.research.stats import mean_cluster
from kht.trading.strategy import EdgeModel, segment_keys

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)

BAND = (0.85, 0.99)       # fitted on a slightly wider band than is traded, for stability
PRIOR_STRENGTH = 150.0    # pseudo-trades pulling a segment toward the pooled estimate
MIN_SEGMENT = 40


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def fit_delta(offset: np.ndarray, won: np.ndarray, iters: int = 60) -> tuple[float, float]:
    """MLE of ``delta`` in sigmoid(offset + delta); returns (delta, naive se)."""
    d = 0.0
    for _ in range(iters):
        mu = 1 / (1 + np.exp(-(offset + d)))
        grad = float((won - mu).sum())
        hess = float((mu * (1 - mu)).sum())
        if hess <= 0:
            break
        step = grad / hess
        d += max(min(step, 1.0), -1.0)
        if abs(step) < 1e-10:
            break
    mu = 1 / (1 + np.exp(-(offset + d)))
    return d, 1 / math.sqrt(max(float((mu * (1 - mu)).sum()), 1e-9))


def fit_line(price: np.ndarray, won: np.ndarray, iters: int = 80) -> tuple[float, float]:
    """MLE of (a, b) in sigmoid(a + b * logit(price))."""
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


def fit_model(t: pd.DataFrame) -> tuple[EdgeModel, pd.DataFrame]:
    """Pooled line plus one shrunken intercept shift per segment."""
    px, won = t["entry_px"].to_numpy(), t["won"].to_numpy()
    a, b = fit_line(px, won)
    rows = [{"segment": "(pooled)", "n": len(t), "shift_raw": 0.0, "shift": 0.0, "se": float("nan"),
             "a": a, "b": b, "win%": 100 * won.mean(), "avg_px": px.mean()}]
    segments: dict[str, tuple[float, float]] = {}
    for col in ("seg_full", "seg_kind", "seg_cat"):
        for key, g in t.groupby(col):
            if len(g) < MIN_SEGMENT:
                continue
            gp, gw = g["entry_px"].to_numpy(), g["won"].to_numpy()
            d_raw, se = fit_delta(a + b * logit(gp), gw)
            w = len(g) / (len(g) + PRIOR_STRENGTH)
            d = w * d_raw                                   # shrunk toward zero = toward the pooled line
            segments[str(key)] = (float(a + d), float(b))
            rows.append({"segment": str(key), "n": len(g), "shift_raw": d_raw, "shift": d, "se": se,
                         "a": a + d, "b": b, "win%": 100 * gw.mean(), "avg_px": gp.mean()})
    return EdgeModel(pooled=(a, b), segments=segments), pd.DataFrame(rows)


def training_trades(s: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    t = candidate_trades(s, Rule(BAND[0], BAND[1], 3, 60))
    info = meta.set_index("market_id")
    cat = info["category"].reindex(t["market_id"]).to_numpy()
    o0 = info["outcome0"].reindex(t["market_id"]).to_numpy()
    neg = info["neg_risk"].reindex(t["market_id"]).fillna(False).to_numpy(dtype=bool)
    keys = [segment_keys(c, o, int(sd), bool(n)) for c, o, sd, n in zip(cat, o0, t["side"], neg)]
    t["seg_full"] = [k[0] for k in keys]
    t["seg_kind"] = [k[1] for k in keys]
    t["seg_cat"] = [k[2] for k in keys]
    t["keys"] = keys
    t["fee_rate"] = t["entry_fee"] / (t["entry_px"] * (1 - t["entry_px"]))
    return t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="config/model.json")
    ap.add_argument("--report", default="reports/research")
    args = ap.parse_args()
    rep = Path(args.report)
    rep.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    meta = load_meta("closed")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    meta = meta[(~meta["category"].isin(["sports", "crypto"])) & (life >= 2) & resolved].copy()
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(build_trades_table(meta)), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    t = training_trades(s, meta)
    print(f"{len(t):,} training trades in {t['cluster'].nunique():,} events "
          f"({pd.to_datetime(t['entry_period'].min() * 86_400, unit='s').date()} .. "
          f"{pd.to_datetime(t['entry_period'].max() * 86_400, unit='s').date()})")

    # ---- walk-forward: refit every quarter on everything that had already
    # *resolved* by then, score the following quarter
    t["q"] = pd.to_datetime(t["entry_period"] * 86_400, unit="s").dt.to_period("Q")
    quarters = sorted(t["q"].unique())
    scored = []
    for q in quarters[2:]:
        cutoff = q.start_time.timestamp() / 86_400
        train = t[t["exit_period"] < cutoff]
        test = t[t["q"] == q]
        if len(train) < 300 or test.empty:
            continue
        model, _ = fit_model(train)
        p = np.array([model.p_win(px, k) for px, k in zip(test["entry_px"], test["keys"])])
        scored.append(test.assign(p_hat=p, pred_edge=p - test["cost"]))
    if scored:
        wf = pd.concat(scored, ignore_index=True)
        wf["bucket"] = pd.qcut(wf["pred_edge"], 4, labels=["lowest", "low", "high", "highest"], duplicates="drop")
        rows = []
        for b, g in wf.groupby("bucket", observed=True):
            r = mean_cluster(g["ret"].to_numpy(), g["cluster"].to_numpy())
            rows.append({"predicted edge": b, "trades": len(g), "avg predicted edge (c)": 100 * g["pred_edge"].mean(),
                         "realised pnl (c)": 100 * g["pnl_ps"].mean(), "avg ret %": 100 * r.mean, "t": r.t,
                         "win %": 100 * (g["pnl_ps"] > 0).mean()})
        wft = pd.DataFrame(rows)
        wft.to_csv(rep / "m_walkforward_by_predicted_edge.csv", index=False)
        print("\nwalk-forward: realised result by the model's predicted edge (out of sample)\n", wft.round(2).to_string(index=False))
        sel = wf[wf["pred_edge"] >= 0.01]
        r_all = mean_cluster(wf["ret"].to_numpy(), wf["cluster"].to_numpy())
        r_sel = mean_cluster(sel["ret"].to_numpy(), sel["cluster"].to_numpy()) if len(sel) > 20 else None
        print(f"\nout-of-sample, all band trades: {100 * r_all.mean:.2f}% (t={r_all.t:.2f}, n={r_all.n}); "
              + (f"model says edge >= 1c: {100 * r_sel.mean:.2f}% (t={r_sel.t:.2f}, n={r_sel.n})" if r_sel else "too few selected"))
        wf.drop(columns=["keys"]).to_csv(rep / "m_walkforward_trades.csv", index=False)

    # ---- final model on everything
    model, table = fit_model(t)
    model.info = {
        "fitted_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()),
        "form": "P(pays) = sigmoid(a + b*logit(ask)); per-segment shift of a, shrunk toward the pooled line",
        "training": f"{len(t)} trades, ask in {BAND}, 3-60 scheduled days to end, non-sports non-crypto, "
                    "markets with >=100k shares already traded",
        "prior_strength": PRIOR_STRENGTH,
    }
    model.save(args.out)
    table.to_csv(rep / "m_model_segments.csv", index=False)
    print("\nfinal model\n", table.round(3).to_string(index=False))
    print(f"\nexample: a 93c ask -> pooled estimate {model.p_win(0.93):.4f}; 96c -> {model.p_win(0.96):.4f}")
    print(f"saved {args.out} ({time.time() - t0:.0f}s)")
    json.dump({"n": int(len(t)), "events": int(t["cluster"].nunique())}, open(rep / "m_model_sample.json", "w"))


if __name__ == "__main__":
    main()

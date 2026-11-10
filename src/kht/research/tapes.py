"""Per-game features from taker-side trade tapes of sports moneyline markets.

A tape row is one taker order: who (wallet), which outcome token, BUY or SELL,
price and size. Everything is re-expressed for *outcome 0*:

    p0   = price            if the trade was in token 0, else 1 - price
    dir0 = +1 if the taker became longer outcome 0 (bought 0 or sold 1), else -1

so a taker buying the other side at 23c shows up as selling outcome 0 at 77c.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..data.download import DATA_DIR


def load_tape(condition_id: str) -> pd.DataFrame | None:
    path = DATA_DIR / "trades" / f"{condition_id}.parquet"
    if not path.exists():
        return None
    t = pd.read_parquet(path)
    if t.empty:
        return None
    idx0 = t["outcome_index"].to_numpy() == 0
    buy = t["side"].to_numpy() == "BUY"
    t["p0"] = np.where(idx0, t["price"], 1.0 - t["price"])
    t["dir0"] = np.where(idx0 == buy, 1.0, -1.0)
    t["usd"] = t["price"] * t["size"]
    return t


def tape_paths() -> list[Path]:
    return sorted((DATA_DIR / "trades").glob("*.parquet"))


def last_price_before(t: pd.DataFrame, ts: float, max_age: float | None = None) -> float:
    """Size-weighted price of the last few trades at or before ``ts`` (outcome 0)."""
    sub = t[t["timestamp"] <= ts]
    if sub.empty:
        return float("nan")
    if max_age is not None and ts - float(sub["timestamp"].iloc[-1]) > max_age:
        return float("nan")
    tail = sub.tail(5)
    return float(np.average(tail["p0"], weights=np.maximum(tail["size"], 1e-9)))


def quote_before(t: pd.DataFrame, ts: float, lookback: float = 6 * 3600) -> tuple[float, float]:
    """Rough (bid, ask) for outcome 0 just before ``ts``: the most recent taker
    sell printed at the bid and the most recent taker buy printed at the ask."""
    sub = t[(t["timestamp"] <= ts) & (t["timestamp"] > ts - lookback)]
    sells = sub.loc[sub["dir0"] < 0, "p0"]
    buys = sub.loc[sub["dir0"] > 0, "p0"]
    bid = float(sells.iloc[-1]) if len(sells) else float("nan")
    ask = float(buys.iloc[-1]) if len(buys) else float("nan")
    return bid, ask


def pregame_features(t: pd.DataFrame, game_start: float, leads_hours: tuple[int, ...] = (1, 3, 6, 12, 24, 48, 72)) -> dict[str, float]:
    """Summarise one game's pre-game trading."""
    pre = t[t["timestamp"] < game_start]
    out: dict[str, float] = {
        "n_trades": float(len(t)),
        "n_pre": float(len(pre)),
        "vol_pre": float(pre["size"].sum()),
        "usd_pre": float(pre["usd"].sum()),
        "vol_total": float(t["size"].sum()),
        "wallets_pre": float(pre["proxy_wallet"].nunique()),
    }
    if pre.empty:
        return out
    out["first_pre_ts"] = float(pre["timestamp"].iloc[0])
    out["p_close"] = last_price_before(pre, game_start)
    bid, ask = quote_before(pre, game_start)
    out["bid_close"], out["ask_close"] = bid, ask
    for h in leads_hours:
        ts = game_start - h * 3600
        out[f"p_{h}h"] = last_price_before(pre, ts)
        win = pre[pre["timestamp"] >= ts]
        signed = win["dir0"] * win["size"]
        out[f"vol_last_{h}h"] = float(win["size"].sum())
        out[f"netflow_last_{h}h"] = float(signed.sum())
        small = win["usd"] < 50
        big = win["usd"] >= 1000
        out[f"netflow_small_last_{h}h"] = float(signed[small].sum())
        out[f"netflow_big_last_{h}h"] = float(signed[big].sum())
        out[f"n_small_last_{h}h"] = float(small.sum())
        out[f"n_big_last_{h}h"] = float(big.sum())
    return out


def build_pregame_table(meta: pd.DataFrame, progress_every: int = 2000) -> pd.DataFrame:
    """One row per sports game market that has a downloaded tape."""
    have = {p.stem for p in tape_paths()}
    sel = meta[meta["condition_id"].isin(have) & meta["game_start_ts"].notna()]
    rows = []
    for i, m in enumerate(sel.itertuples(index=False)):
        t = load_tape(m.condition_id)
        if t is None:
            continue
        f = pregame_features(t, float(m.game_start_ts))
        f.update(
            market_id=m.market_id, condition_id=m.condition_id, event_id=m.event_id, question=m.question,
            game_start_ts=m.game_start_ts, start_ts=m.start_ts, winner=m.winner, volume=m.volume,
            fee_rate=m.fee_rate, neg_risk=m.neg_risk, tags=m.tags, outcome0=m.outcome0, outcome1=m.outcome1,
        )
        rows.append(f)
        if progress_every and (i + 1) % progress_every == 0:
            print(f"  tapes processed: {i + 1}/{len(sel)}", flush=True)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["payoff"] = np.where(df["winner"] == 0, 1.0, np.where(df["winner"] == 1, 0.0, np.nan))
    df["cluster"] = np.where(df["event_id"] >= 0, df["event_id"], -df["market_id"])
    df["day"] = (df["game_start_ts"] // 86_400).astype(int)
    return df


LEAGUE_TAGS = ["nfl", "nba", "mlb", "nhl", "cfb", "ncaa-basketball", "wnba", "tennis", "soccer", "esports",
               "ufc", "cricket"]


def league_of(tags: str) -> str:
    parts = set((tags or "").split("|"))
    for name in LEAGUE_TAGS:
        if name in parts:
            return name
    return "other"

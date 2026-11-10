"""Sports pre-game research: one long table of pre-game trades, and game-level
features built from it.

The unit of analysis is a head-to-head game-winner (moneyline) market with a
scheduled start. Everything is expressed for outcome 0 (see ``tapes.py``):
``p0`` is the price of outcome 0 implied by the trade and ``dir0`` is +1 when
the taker got longer outcome 0.

Universe rule (important). Markets were downloaded if their *total* volume was
at least 100k shares, and total volume includes in-game trading, which is much
heavier in games with comebacks and upsets. Selecting on it makes underdogs
look underpriced. Every analysis here therefore keeps a game only if its
*pre-game* volume alone clears the bar: a condition known before kickoff that
also guarantees the game is in the download regardless of what happened later.
"""

from __future__ import annotations

import concurrent.futures as cf
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.download import DATA_DIR

PRE_VOLUME_FLOOR = 100_000  # shares traded before kickoff


def _one_tape(args: tuple[str, int, float]) -> pd.DataFrame | None:
    condition_id, market_id, game_start = args
    path = DATA_DIR / "trades" / f"{condition_id}.parquet"
    if not path.exists():
        return None
    t = pd.read_parquet(path)
    if t.empty:
        return None
    t = t[t["timestamp"] < game_start]
    if t.empty:
        return None
    idx0 = t["outcome_index"].to_numpy() == 0
    buy = t["side"].to_numpy() == "BUY"
    price = t["price"].to_numpy()
    return pd.DataFrame(
        {
            "market_id": np.int64(market_id),
            "ts": t["timestamp"].to_numpy(dtype=np.int64),
            "lead_s": (game_start - t["timestamp"].to_numpy()).astype(np.float32),
            "p0": np.where(idx0, price, 1.0 - price).astype(np.float32),
            "dir0": np.where(idx0 == buy, 1, -1).astype(np.int8),
            "size": t["size"].to_numpy(dtype=np.float32),
            "usd": (price * t["size"].to_numpy()).astype(np.float32),
            "wallet": t["proxy_wallet"].to_numpy(),
        }
    )


def build_pregame_trades(meta: pd.DataFrame, workers: int = 4) -> pd.DataFrame:
    """Concatenate the pre-game part of every downloaded sports moneyline tape."""
    have = {p.stem for p in (DATA_DIR / "trades").glob("*.parquet")}
    sel = meta[meta["condition_id"].isin(have) & meta["game_start_ts"].notna()]
    jobs = list(zip(sel["condition_id"], sel["market_id"].astype(int), sel["game_start_ts"].astype(float)))
    parts: list[pd.DataFrame] = []
    with cf.ProcessPoolExecutor(max_workers=workers) as pool:
        for part in pool.map(_one_tape, jobs, chunksize=200):
            if part is not None:
                parts.append(part)
    df = pd.concat(parts, ignore_index=True)
    codes, _ = pd.factorize(df["wallet"])
    df["wallet"] = codes.astype(np.int32)
    return df.sort_values(["market_id", "ts"], kind="stable").reset_index(drop=True)


def save_pregame_trades(df: pd.DataFrame) -> Path:
    out = DATA_DIR / "derived" / "sports_pregame_trades.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return out


def load_pregame_trades() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "derived" / "sports_pregame_trades.parquet")


# ------------------------------------------------------------ game features
LEADS_H = (72, 48, 24, 12, 6, 3, 1, 0)


def _quote_asof(tr: pd.DataFrame, lead_h: float, lookback_h: float = 12.0, max_spread: float = 0.06) -> pd.DataFrame:
    """Bid/ask/mid proxy per market as of ``lead_h`` hours before kickoff.

    The last taker sell printed at (about) the bid and the last taker buy at
    (about) the ask. A mid is only reported when both are recent and the
    implied spread is sane; otherwise it is NaN rather than a guess.
    """
    lo, hi = lead_h * 3600.0, (lead_h + lookback_h) * 3600.0
    w = tr[(tr["lead_s"] > lo) & (tr["lead_s"] <= hi)]
    last_sell = w[w["dir0"] < 0].groupby("market_id")["p0"].last().rename("bid")
    last_buy = w[w["dir0"] > 0].groupby("market_id")["p0"].last().rename("ask")
    last_any = w.groupby("market_id")["p0"].last().rename("last")
    q = pd.concat([last_sell, last_buy, last_any], axis=1)
    spread = q["ask"] - q["bid"]
    ok = (spread >= -0.005) & (spread <= max_spread)
    q["mid"] = np.where(ok, 0.5 * (q["ask"] + q["bid"]), np.nan)
    q["spread"] = np.where(ok, spread.clip(lower=0), np.nan)
    return q.add_suffix(f"_{lead_h:g}h")


def _flow_window(tr: pd.DataFrame, far_h: float, near_h: float, label: str) -> pd.DataFrame:
    """Order-flow summary for trades between ``far_h`` and ``near_h`` hours before kickoff."""
    w = tr[(tr["lead_s"] > near_h * 3600.0) & (tr["lead_s"] <= far_h * 3600.0)].copy()
    w["signed"] = w["dir0"] * w["size"]
    w["signed_usd"] = w["dir0"] * w["usd"]
    w["small"] = w["usd"] < 50
    w["big"] = w["usd"] >= 1000
    w["buy0"] = w["dir0"] > 0
    g = w.groupby("market_id")
    out = pd.DataFrame({
        "vol": g["size"].sum(),
        "usd": g["usd"].sum(),
        "n": g.size(),
        "net": g["signed"].sum(),
        "net_usd": g["signed_usd"].sum(),
        "tickets0": g["buy0"].mean(),                         # share of taker orders backing outcome 0
    })
    small = w[w["small"]].groupby("market_id")
    big = w[w["big"]].groupby("market_id")
    out["n_small"] = small.size()
    out["net_small_usd"] = small["signed_usd"].sum()
    out["usd_small"] = small["usd"].sum()
    out["tickets0_small"] = small["buy0"].mean()
    out["n_big"] = big.size()
    out["net_big_usd"] = big["signed_usd"].sum()
    out["usd_big"] = big["usd"].sum()
    # distinct bettors on each side: the 'percent of tickets' sportsbooks publish
    wallets = w.groupby(["market_id", "buy0"])["wallet"].nunique().unstack(fill_value=0)
    out["wallets0"] = wallets.get(True, 0)
    out["wallets1"] = wallets.get(False, 0)
    return out.add_suffix(f"_{label}")


def game_features(tr: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """One row per game: quote proxies at fixed leads, flows between them, outcome."""
    g = tr.groupby("market_id")
    base = pd.DataFrame({
        "vol_pre": g["size"].sum(),
        "usd_pre": g["usd"].sum(),
        "n_pre": g.size(),
        "wallets_pre": g["wallet"].nunique(),
        "first_lead_h": g["lead_s"].max() / 3600.0,
    })
    parts = [base] + [_quote_asof(tr, h) for h in LEADS_H]
    windows = [(1e6, 72, "to72"), (72, 24, "72_24"), (24, 6, "24_6"), (6, 1, "6_1"), (1, 0, "1_0"),
               (24, 0, "24_0"), (1e6, 24, "to24"), (1e6, 6, "to6"), (1e6, 0, "all")]
    parts += [_flow_window(tr, far, near, label) for far, near, label in windows]
    feat = pd.concat(parts, axis=1)          # outer join on market_id, done once
    cols = ["market_id", "condition_id", "event_id", "question", "game_start_ts", "start_ts", "winner", "volume",
            "fee_rate", "neg_risk", "tags", "outcome0", "outcome1"]
    feat = feat.join(meta.set_index("market_id")[cols[1:]], how="left").reset_index().copy()
    feat["payoff"] = np.where(feat["winner"] == 0, 1.0, np.where(feat["winner"] == 1, 0.0, np.nan))
    from .tapes import league_of

    extra = pd.DataFrame({
        "cluster": np.where(feat["event_id"] >= 0, feat["event_id"], -feat["market_id"]),
        "day": (feat["game_start_ts"] // 86_400).astype(int),
        "league": feat["tags"].map(league_of),
        "clean": feat["vol_pre"] >= PRE_VOLUME_FLOOR,
    }, index=feat.index)
    return pd.concat([feat, extra], axis=1)


# ------------------------------------------------------------ who loses money?
def taker_pnl_table(tr: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """Per-trade profit of the *taker* if the position is held to resolution.

    For a taker who bought a token at price ``x``: profit per share is
    ``payoff - x`` (before the taker fee). In outcome-0 terms that is
    ``dir0 * (payoff0 - p0)``. The maker on the other side earns the negative.

    ``x`` (the price the taker paid for the side they backed) is the natural
    longshot/favourite axis: x < 0.5 means the taker backed the underdog.
    """
    g = games.set_index("market_id")
    t = tr[tr["market_id"].isin(g.index[g["clean"] & g["payoff"].notna()])].copy()
    payoff = g["payoff"].reindex(t["market_id"]).to_numpy()
    p0 = t["p0"].to_numpy(dtype=np.float64)
    d = t["dir0"].to_numpy()
    t["taker_px"] = np.where(d > 0, p0, 1.0 - p0)                 # price paid for the backed side
    t["taker_won"] = np.where(d > 0, payoff, 1.0 - payoff)
    t["pnl_ps"] = t["taker_won"] - t["taker_px"]                  # profit per share, pre-fee
    t["pnl_usd"] = t["pnl_ps"] * t["size"]
    t["cluster"] = g["cluster"].reindex(t["market_id"]).to_numpy()
    t["day"] = g["day"].reindex(t["market_id"]).to_numpy()
    t["league"] = g["league"].reindex(t["market_id"]).to_numpy()
    t["fee_rate"] = g["fee_rate"].reindex(t["market_id"]).to_numpy()
    t["lead_h"] = t["lead_s"] / 3600.0
    return t


def weighted_mean_cluster(value: np.ndarray, weight: np.ndarray, cluster: np.ndarray) -> tuple[float, float, int]:
    """Ratio estimate sum(w*v)/sum(w) with a cluster-robust (linearised) SE."""
    ok = np.isfinite(value) & np.isfinite(weight) & (weight > 0)
    v, w, c = value[ok], weight[ok], cluster[ok]
    if len(v) < 2:
        return float("nan"), float("nan"), 0
    est = float((w * v).sum() / w.sum())
    codes, uniq = pd.factorize(c)
    score = np.bincount(codes, weights=w * (v - est), minlength=len(uniq))
    g = len(uniq)
    se = float(np.sqrt(g / max(g - 1, 1) * (score**2).sum()) / w.sum())
    return est, se, g


# ------------------------------------------------------- generic trade table
def _one_tape_full(args: tuple[str, int, bool]) -> pd.DataFrame | None:
    condition_id, market_id, with_wallet = args
    path = DATA_DIR / "trades" / f"{condition_id}.parquet"
    if not path.exists():
        return None
    cols = ["timestamp", "side", "outcome_index", "price", "size"] + (["proxy_wallet"] if with_wallet else [])
    t = pd.read_parquet(path, columns=cols)
    if t.empty:
        return None
    idx0 = t["outcome_index"].to_numpy() == 0
    buy = t["side"].to_numpy() == "BUY"
    price = t["price"].to_numpy()
    out = pd.DataFrame(
        {
            "market_id": np.int64(market_id),
            "ts": t["timestamp"].to_numpy(dtype=np.int64),
            "p0": np.where(idx0, price, 1.0 - price).astype(np.float32),
            "dir0": np.where(idx0 == buy, 1, -1).astype(np.int8),
            "size": t["size"].to_numpy(dtype=np.float32),
            "usd": (price * t["size"].to_numpy()).astype(np.float32),
        }
    )
    if with_wallet:
        out["wallet"] = t["proxy_wallet"].to_numpy()
    return out


def build_trades_table(meta: pd.DataFrame, workers: int = 4, with_wallet: bool = False) -> pd.DataFrame:
    """Every downloaded trade of the given markets, in outcome-0 terms, plus
    ``cum_before``: shares traded in that market *before* the trade.

    ``cum_before`` is what makes an honest universe possible: an observation
    at time t may be used only if the market had already traded enough by t.
    It is computed backward from the market's total volume, so it is correct
    even for tapes that were truncated to their most recent pages.

    Wallet ids are large (tens of millions of strings); they are only loaded
    when asked for.
    """
    have = {p.stem for p in (DATA_DIR / "trades").glob("*.parquet")}
    sel = meta[meta["condition_id"].isin(have)]
    jobs = [(c, int(m), with_wallet) for c, m in zip(sel["condition_id"], sel["market_id"])]
    parts: list[pd.DataFrame] = []
    with cf.ProcessPoolExecutor(max_workers=workers) as pool:
        for part in pool.map(_one_tape_full, jobs, chunksize=200):
            if part is not None:
                parts.append(part)
    df = pd.concat(parts, ignore_index=True)
    del parts
    if with_wallet:
        codes, _ = pd.factorize(df["wallet"])
        df["wallet"] = codes.astype(np.int32)
    df = df.sort_values(["market_id", "ts"], kind="stable").reset_index(drop=True)
    total = meta.set_index("market_id")["volume"].reindex(df["market_id"]).to_numpy()
    size = df["size"].to_numpy(dtype=np.float64)
    # shares traded at or after each row, within its market
    rev = pd.Series(size[::-1]).groupby(df["market_id"].to_numpy()[::-1], sort=False).cumsum().to_numpy()[::-1]
    df["cum_before"] = np.maximum(total - rev, 0.0).astype(np.float32)
    return df

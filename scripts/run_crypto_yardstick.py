"""Track C2 of the second round, discovery set only: does an outside yardstick
find mispriced crypto price markets?

For every taker print in a crypto price market, work out what the bet was
worth from the coin's price and the options market's volatility index, using
only candles that had closed before the print, and ask whether the gap
between that value and the price paid predicts the profit.

Three things are reported, all on markets scheduled to end before 1 June 2026
(the holdout is not read):

  1. Calibration: how often things happened against the model's probability.
  2. The gap: profit per share against (model value - price - fee), per print.
     The same table is printed from day-end quotes, where the price can be
     hours older than the coin price it is compared with. That version looks
     like a strong result and is an artefact; it is kept as a warning.
  3. Distance: near-certain "No" contracts on price barriers, filtered by how
     many expected moves away the barrier is, as one trade per market.

    python scripts/run_crypto_yardstick.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_crypto_price as cp  # noqa: E402

from kht.backtest.harvest import Rule, candidate_trades, prepare  # noqa: E402
from kht.research.crypto import prob_above, prob_touch, prob_yes, realised_vol, sigmas_away  # noqa: E402
from kht.research.sports import build_trades_table  # noqa: E402
from kht.research.stats import mean_cluster, ols_cluster  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
DATA = ROOT / "data" / "crypto"
COINS = ("bitcoin", "ethereum", "solana", "xrp")
EDGE_BINS = [-1, -0.10, -0.05, -0.02, -0.005, 0.005, 0.02, 0.05, 0.10, 1]


class Market:
    """Hourly prices and volatility for the coins, looked up without using the future."""

    def __init__(self) -> None:
        self.px = {c: pd.read_parquet(DATA / f"{c}_1h.parquet") for c in COINS}
        self.dvol = {"bitcoin": pd.read_parquet(DATA / "dvol_BTC.parquet"), "ethereum": pd.read_parquet(DATA / "dvol_ETH.parquet")}
        self.rv = {c: realised_vol(d["close"].to_numpy()) for c, d in self.px.items()}

    def last_closed(self, coin: str, ts: np.ndarray) -> np.ndarray:
        """Index of the last hourly candle that had closed at each time."""
        t = self.px[coin]["ts"].to_numpy()
        return np.clip(np.searchsorted(t, ts, side="right") - 1, 0, len(t) - 1)

    def spot_sigma(self, coin: str, ts: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        i = self.last_closed(coin, ts)
        spot = self.px[coin]["close"].to_numpy()[i]
        dv = self.dvol.get(coin, self.dvol["bitcoin"])
        j = np.clip(np.searchsorted(dv["ts"].to_numpy(), ts, side="right") - 1, 0, len(dv) - 1)
        sigma = dv["close"].to_numpy()[j] / 100.0
        if coin not in self.dvol:
            # no volatility index of its own: Bitcoin's, scaled by how much more the coin has been moving
            sigma = sigma * np.clip(self.rv[coin][i] / self.rv["bitcoin"][self.last_closed("bitcoin", ts)], 0.8, 3.0)
        return spot, sigma, self.rv[coin][i]

    def extreme_since(self, coin: str, start_ts: float, ts: np.ndarray, up: bool) -> np.ndarray:
        """Highest high (or lowest low) from the market's opening to the last closed candle at each time."""
        d = self.px[coin]
        t = d["ts"].to_numpy()
        a = int(np.searchsorted(t, start_ts, side="right"))
        i = self.last_closed(coin, ts)
        hi_i = int(i.max()) + 1
        if hi_i <= a:
            return np.full(len(ts), np.nan)
        run = np.maximum.accumulate(d["high"].to_numpy()[a:hi_i]) if up else np.minimum.accumulate(d["low"].to_numpy()[a:hi_i])
        return np.where(i >= a, run[np.clip(i - a, 0, len(run) - 1)], np.nan)


def attach_model(df: pd.DataFrame, mk: Market) -> pd.DataFrame:
    """Add spot, sigma, whether the barrier has been touched, and the model's probability of Yes.
    ``df`` needs market_id, ts, coin, kind, strike, strike_hi, start_ts, end_ts and is sorted by market."""
    n = len(df)
    spot, sigma, rv, ext = (np.full(n, np.nan) for _ in range(4))
    ts = df["ts"].to_numpy()
    coin = df["coin"].to_numpy()
    kind = df["kind"].to_numpy()
    for c in COINS:
        m = coin == c
        if m.any():
            spot[m], sigma[m], rv[m] = mk.spot_sigma(c, ts[m])
    mid = df["market_id"].to_numpy()
    start = df["start_ts"].to_numpy()
    bounds = np.flatnonzero(np.diff(mid)) + 1
    for a, b in zip(np.concatenate(([0], bounds)), np.concatenate((bounds, [n]))):
        if kind[a] in ("reach", "dip") and coin[a] in COINS:
            ext[a:b] = mk.extreme_since(coin[a], float(start[a]), ts[a:b], up=kind[a] == "reach")
    strike = df["strike"].to_numpy()
    years = (df["end_ts"].to_numpy() - ts) / (365 * 86_400)
    touched = ((kind == "reach") & (ext >= strike)) | ((kind == "dip") & (ext <= strike))
    p_yes = np.where(kind == "above", prob_above(spot, strike, sigma, years), prob_touch(spot, strike, sigma, years))
    out = df.copy()
    out["spot"], out["sigma"], out["rv"], out["years"], out["touched"] = spot, sigma, rv, years, touched
    out["p_yes"] = np.where(touched, 1.0, p_yes)
    out["z"] = np.abs(sigmas_away(spot, strike, sigma, years))
    return out


def gap_table(d: pd.DataFrame, value: str, label: str, rows_name: str) -> pd.DataFrame:
    r = ols_cluster(d[value].to_numpy(), d[["edge"]].to_numpy(), d["cluster"].to_numpy())
    print(f"\n{label}: profit per share on the model's edge, slope {r.beta[1]:+.3f} (t = {r.t[1]:.2f}); "
          f"{len(d):,} {rows_name} in {d['market_id'].nunique():,} markets, {d['cluster'].nunique()} weeks")
    rows = []
    for b, g in d.assign(eb=pd.cut(d["edge"], EDGE_BINS)).groupby("eb", observed=True):
        m = mean_cluster(g[value].to_numpy(), g["cluster"].to_numpy())
        rows.append({"model value minus price and fee": str(b), rows_name: len(g), "avg price": g["price"].mean(),
                     "model probability": g["p_model"].mean(), "won": g["won"].mean(),
                     "profit, cents a share": 100 * m.mean, "t_week": m.t})
    t = pd.DataFrame(rows)
    print(t.round(3).to_string(index=False))
    return t.assign(table=label)


def main() -> None:
    meta = cp.crypto_price_meta()
    meta = meta[meta["kind"].isin(["above", "reach", "dip"]) & (meta["end_ts"] < cp.SPLIT_TS)
                & ~meta["neg_risk"].fillna(False).astype(bool) & meta["coin"].isin(COINS)]
    info = meta.set_index("market_id")
    mk = Market()
    print(f"discovery set, markets on a price at a date or a price barrier, not legs: {len(meta):,}")

    # ------------------------------------------------------------ day-end panel
    s = cp.panel(meta)
    for col in ("coin", "kind", "strike", "strike_hi", "start_ts"):
        s[col] = info[col].reindex(s["market_id"]).to_numpy()
    s = attach_model(s, mk)
    s = s[s["spot"].notna() & (s["years"] > 0)].reset_index(drop=True)
    s["p_model"] = np.where(s["side"] == 0, s["p_yes"], 1 - s["p_yes"])
    s["price"] = s["ask"]
    s["edge"] = s["p_model"] - s["ask"] - s["fee_ps"]

    # 1. calibration, one row per market-day (the Yes side), barrier not yet touched
    y = s[(s["side"] == 0) & ~s["touched"] & (s["days_to_end"] > 3) & (s["days_to_end"] <= 60)].copy()
    y["bin"] = pd.cut(y["p_yes"], [0, 0.005, 0.02, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 0.95, 1.0])
    cal = (y.groupby(["kind", "bin"], observed=True)
            .agg(market_days=("won", "size"), markets=("market_id", "nunique"), model=("p_yes", "mean"), happened=("won", "mean"),
                 polymarket_last_price=("last", "mean")).round(3).reset_index())
    cal.to_csv(OUT / "cy_calibration.csv", index=False)
    print("\n1. Calibration, 3-60 days to the end: the model's probability, how often it happened, and Polymarket's last price")
    print(cal.to_string(index=False))

    # 2a. the artefact: day-end quotes against the coin price at the end of the day
    d = s[s["ask"].notna() & ~s["touched"] & (s["days_to_end"] > 3) & (s["days_to_end"] <= 60)]
    art = gap_table(d.assign(won=d["won"]), "net_ps", "2a. ARTEFACT, day-end quotes (the price can be hours older than the coin price beside it), 3-60 days",
                    "outcome_days")

    # 2b. the honest version: every print, model from candles closed before it
    tr = build_trades_table(meta)
    tr = tr[tr["cum_before"] >= 100_000].reset_index(drop=True)
    for col in ("coin", "kind", "strike", "strike_hi", "start_ts", "end_ts", "winner"):
        tr[col] = info[col].reindex(tr["market_id"]).to_numpy()
    tr = tr[tr["winner"].notna() & (tr["end_ts"] - tr["ts"] > 3600)].reset_index(drop=True)
    tr = attach_model(tr, mk)
    side = np.where(tr["dir0"] > 0, 0, 1)
    tr["price"] = np.where(side == 0, tr["p0"], 1 - tr["p0"]).astype(float)
    tr["won"] = (side == tr["winner"].to_numpy()).astype(float)
    tr["p_model"] = np.where(side == 0, tr["p_yes"], 1 - tr["p_yes"])
    fee = 0.07 * tr["price"] * (1 - tr["price"])
    tr["edge"] = tr["p_model"] - tr["price"] - fee
    tr["profit"] = tr["won"] - tr["price"] - fee
    tr["cluster"] = (tr["end_ts"] // cp.WEEK).astype(np.int64)
    tr["dte"] = tr["years"] * 365
    u = tr[~tr["touched"] & (tr["price"] > 0.02) & (tr["price"] < 0.98)]
    print(f"\n{len(tr):,} taker prints; {len(u):,} at 2-98c with the barrier not yet touched")
    parts = [art,
             gap_table(u[(u["dte"] > 3) & (u["dte"] <= 60)], "profit", "2b. Every print, 3-60 days to the end", "prints"),
             gap_table(u[(u["dte"] > 1) & (u["dte"] <= 3)], "profit", "2b. Every print, 1-3 days to the end", "prints"),
             gap_table(u[(u["dte"] > 1 / 24) & (u["dte"] <= 1)], "profit", "2b. Every print, 1 hour to 1 day to the end", "prints")]
    for k in ("above", "reach", "dip"):
        parts.append(gap_table(u[(u["dte"] > 1) & (u["dte"] <= 60) & (u["kind"] == k)], "profit", f"2b. Every print, 1-60 days, {k} only", "prints"))
    pd.concat(parts, ignore_index=True).to_csv(OUT / "cy_model_gap.csv", index=False)

    # 3. near-certain contracts on barriers, by distance, one trade per market at a later print
    s = prepare(s)
    ask, dte, z, kind = (s[c].to_numpy() for c in ("ask", "days_to_end", "z", "kind"))
    barrier = np.isin(kind, ["reach", "dip"]) & ~s["touched"].to_numpy()
    rule = Rule(0.90, 0.985, 3, 60)
    in_band = (ask > 0.90) & (ask <= 0.985) & (dte > 3) & (dte <= 60)
    rows = []
    kept = {}
    for label, sig in [("any distance", barrier)] + [(f"{zmin} or more expected moves away", barrier & (z >= zmin)) for zmin in (2.0, 2.5, 3.0, 3.5, 4.0)] + [
            ("reach only, 2.5 or more", barrier & (kind == "reach") & (z >= 2.5)), ("dip only, 2.5 or more", barrier & (kind == "dip") & (z >= 2.5))]:
        t = candidate_trades(s, rule, signal=sig & in_band)
        kept[label] = t
        rows.append({"barrier markets, 90-98.5c, 3-60 days": label, **cp.stats(t)})
    dist = pd.DataFrame(rows)
    dist.to_csv(OUT / "cy_distance_rules.csv", index=False)
    print("\n3. Near-certain contracts on price barriers, by distance (one trade per market, bought at a later print)")
    print(dist.round(2).to_string(index=False))
    t = kept["3.0 or more expected moves away"].copy()
    t["entry"] = pd.to_datetime(t["entry_period"], unit="D").dt.date
    lost = t[t["won"] == 0]
    print("\nthe losing trades at 3.0 or more expected moves away:")
    print(lost.assign(question=lost["market_id"].map(info["question"]))[["entry", "entry_px", "dte_at_signal", "question"]].to_string(index=False))
    all_t = kept["any distance"].copy()
    all_t["quarter"] = pd.to_datetime(all_t["entry_period"], unit="D").dt.to_period("Q").astype(str)
    all_t["kind"] = all_t["market_id"].map(info["kind"])
    by_q = all_t.groupby(["quarter", "kind"]).agg(trades=("won", "size"), lost=("won", lambda w: int((w == 0).sum())),
                                                    avg_ret_pct=("ret", lambda r: 100 * r.mean())).round(2)
    btc = mk.px["bitcoin"].assign(quarter=pd.to_datetime(mk.px["bitcoin"]["ts"], unit="s").dt.to_period("Q").astype(str))
    move = btc.groupby("quarter")["close"].agg(lambda c: 100 * (c.iloc[-1] / c.iloc[0] - 1)).round(0).rename("bitcoin_change_pct")
    by_q = by_q.reset_index().merge(move.reset_index(), on="quarter", how="left")
    by_q.to_csv(OUT / "cy_by_quarter.csv", index=False)
    print("\nnear-certain barrier contracts by quarter and kind, beside Bitcoin's change over the quarter:")
    print(by_q.to_string(index=False))


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for st in self.streams:
            st.write(text)

    def flush(self):
        for st in self.streams:
            st.flush()


if __name__ == "__main__":
    with (OUT / "crypto_yardstick_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__

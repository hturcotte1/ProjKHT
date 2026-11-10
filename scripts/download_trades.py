"""Download taker-side trade tapes for a named subset of resolved markets.

Usage:
    python scripts/download_trades.py sports_ml [--rate 10] [--limit N]

Tapes land in data/trades/<condition_id>.parquet and are skipped if present.
"""

from __future__ import annotations

import argparse

import pandas as pd

from kht.api import Http, Polymarket
from kht.data.download import download_trades_many, load_meta, log


def subset(meta: pd.DataFrame, name: str) -> pd.DataFrame:
    if name == "sports_ml":
        # head-to-head game winners with a known kickoff: the cleanest setting
        # for studying pre-game opinion
        sel = (meta["category"] == "sports") & (meta["sports_type"] == "moneyline") & meta["game_start_ts"].notna()
    elif name == "non_sports":
        life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
        # split (50/50) resolutions are kept: for a 93c position they are a real loss
        resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
        sel = (meta["category"] != "sports") & (meta["category"] != "crypto") & (life >= 2) & resolved
    elif name == "crypto_price":
        # A price on a date ("above", "below", "between") or a price touched
        # within a period ("reach", "hit", "dip to"). The five-minute, hourly
        # and daily "up or down" markets are left out.
        life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
        resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
        q = meta["question"].str.lower()
        price_q = q.str.contains(r"\b(?:above|below|greater than|less than|between|hit|reach|dip to|fall to|drop to)\b")
        sel = (meta["category"] == "crypto") & ~q.str.contains("up or down") & price_q & (life >= 2) & resolved
    elif name == "sports_other":
        # Season-long, tournament and other sports questions that are not a
        # single game: the long-lived markets the first round never looked at.
        life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
        resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
        not_game = ~meta["is_game"].fillna(False).astype(bool) & meta["game_start_ts"].isna()
        sel = (meta["category"] == "sports") & not_game & (life >= 14) & resolved
    elif name == "non_sports_thin":
        # The same kind of market as "non_sports", from the list of markets that
        # traded 20,000 to 100,000 shares (data/meta/closed_thin.parquet).
        life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
        resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
        sel = (meta["category"] != "sports") & (meta["category"] != "crypto") & (life >= 2) & resolved
    elif name == "open_non_sports":
        # still-open markets: needed so that results are not conditioned on
        # 'the market has already resolved' (censoring)
        sel = (meta["category"] != "sports") & (meta["category"] != "crypto")
    else:
        raise SystemExit(f"unknown subset {name}")
    return meta.loc[sel]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("subset")
    ap.add_argument("--rate", type=float, default=10.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--max-pages", type=int, default=400)
    ap.add_argument("--max-volume", type=float, default=None, help="skip markets above this share volume")
    ap.add_argument("--shard", default=None, help="i/n: take every n-th market starting at i (run n processes in parallel)")
    args = ap.parse_args()

    source = "open" if args.subset.startswith("open") else "closed_thin" if args.subset.endswith("_thin") else "closed"
    meta = subset(load_meta(source), args.subset)
    if args.max_volume:
        meta = meta[meta["volume"] <= args.max_volume]
    # newest first: recent markets reflect today's fee and liquidity regime
    meta = meta.sort_values("closed_ts", ascending=False, na_position="first")
    if args.limit:
        meta = meta.head(args.limit)
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        meta = meta.iloc[i::n]
    log(f"{args.subset}: {len(meta)} markets, total volume {meta['volume'].sum() / 1e9:.2f}B shares")
    pm = Polymarket(Http(rate_per_host={"data-api.polymarket.com": args.rate}))
    download_trades_many(pm, meta["condition_id"].tolist(), workers=args.workers, max_pages=args.max_pages)


if __name__ == "__main__":
    main()

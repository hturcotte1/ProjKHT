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
        sel = (meta["category"] != "sports") & (meta["category"] != "crypto") & (life >= 2) & meta["winner"].notna()
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
    args = ap.parse_args()

    meta = subset(load_meta("open" if args.subset.startswith("open") else "closed"), args.subset)
    if args.max_volume:
        meta = meta[meta["volume"] <= args.max_volume]
    # newest first: recent markets reflect today's fee and liquidity regime
    meta = meta.sort_values("closed_ts", ascending=False, na_position="first")
    if args.limit:
        meta = meta.head(args.limit)
    log(f"{args.subset}: {len(meta)} markets, total volume {meta['volume'].sum() / 1e9:.2f}B shares")
    pm = Polymarket(Http(rate_per_host={"data-api.polymarket.com": args.rate}))
    download_trades_many(pm, meta["condition_id"].tolist(), workers=args.workers, max_pages=args.max_pages)


if __name__ == "__main__":
    main()

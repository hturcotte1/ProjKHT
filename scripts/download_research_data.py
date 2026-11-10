"""Download the research dataset (metadata + price histories).

Usage:
    python scripts/download_research_data.py meta   [--min-volume 100000]
    python scripts/download_research_data.py prices [--grain 3h]

The raw data lands under ./data (git-ignored). Both stages are resumable.
"""

from __future__ import annotations

import argparse

import pandas as pd

from kht.api import Polymarket
from kht.data.download import download_market_meta, download_price_panel, load_meta, log

GRAINS = {"3h": 10_800, "12h": 43_200}


def select_for_panel(meta: pd.DataFrame, min_life_days: float = 2.0) -> pd.DataFrame:
    """Markets worth a multi-day price panel: resolved, and alive long enough
    for a 3-hour series to say something (drops the 5-minute / hourly / daily
    crypto and finance 'up or down' markets)."""
    life_days = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    keep = meta["closed"] & (life_days >= min_life_days) & meta["winner"].notna()
    return meta.loc[keep].reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["meta", "prices"])
    ap.add_argument("--min-volume", type=float, default=100_000)
    ap.add_argument("--grain", choices=sorted(GRAINS), default="3h")
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    pm = Polymarket()
    if args.stage == "meta":
        download_market_meta(pm, "closed", closed=True, volume_num_min=args.min_volume)
    else:
        meta = load_meta("closed")
        panel = select_for_panel(meta)
        log(f"panel universe: {len(panel)} of {len(meta)} closed markets")
        download_price_panel(pm, panel, grain=args.grain, bucket_seconds=GRAINS[args.grain], workers=args.workers)


if __name__ == "__main__":
    main()

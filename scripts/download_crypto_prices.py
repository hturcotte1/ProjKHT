"""Hourly coin prices and the options market's volatility index, for track C.

Prices: hourly candles from Binance's public market-data mirror
(data-api.binance.vision), the exchange Polymarket's crypto price markets
resolve on. Volatility: Deribit's DVOL index for Bitcoin and Ether, the
options market's own 30-day forecast, quoted in annualised percent.

Both are public and need no account. Files land in data/crypto/.

    python scripts/download_crypto_prices.py [--start 2024-06-01]
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "crypto"
SYMBOLS = {"bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "solana": "SOLUSDT", "xrp": "XRPUSDT", "dogecoin": "DOGEUSDT",
           "bnb": "BNBUSDT"}
UA = {"User-Agent": "research-client"}


def klines(symbol: str, start_ms: int, end_ms: int, interval: str = "1h") -> pd.DataFrame:
    rows: list[list] = []
    cur = start_ms
    while cur < end_ms:
        r = requests.get("https://data-api.binance.vision/api/v3/klines",
                         params={"symbol": symbol, "interval": interval, "startTime": cur, "endTime": end_ms, "limit": 1000},
                         headers=UA, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows += batch
        cur = int(batch[-1][0]) + 1
        time.sleep(0.15)
    df = pd.DataFrame(rows, columns=["open_ms", "open", "high", "low", "close", "volume", "close_ms", "quote_volume",
                                     "trades", "taker_base", "taker_quote", "ignore"])
    df = df[["open_ms", "open", "high", "low", "close", "volume"]].astype(float)
    df["ts"] = (df["open_ms"] // 1000).astype("int64") + 3600        # the candle's closing time
    return df.drop(columns="open_ms").drop_duplicates("ts").sort_values("ts").reset_index(drop=True)


def dvol(currency: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Hourly DVOL candles (open, high, low, close), newest first from the API."""
    rows: list[list] = []
    end = end_ms
    while end > start_ms:
        r = requests.get("https://www.deribit.com/api/v2/public/get_volatility_index_data",
                         params={"currency": currency, "start_timestamp": start_ms, "end_timestamp": end, "resolution": 3600},
                         headers=UA, timeout=30)
        r.raise_for_status()
        res = r.json()["result"]
        data = res.get("data") or []
        if not data:
            break
        rows += data
        cont = res.get("continuation")
        if not cont or int(cont) >= end:
            break
        end = int(cont)
        time.sleep(0.2)
    df = pd.DataFrame(rows, columns=["ms", "open", "high", "low", "close"]).astype(float)
    df["ts"] = (df["ms"] // 1000).astype("int64") + 3600
    return df.drop(columns="ms").drop_duplicates("ts").sort_values("ts").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2024-06-01")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    start_ms = int(pd.Timestamp(args.start, tz="UTC").timestamp() * 1000)
    end_ms = int(time.time() * 1000)
    for coin, symbol in SYMBOLS.items():
        df = klines(symbol, start_ms, end_ms)
        df.to_parquet(OUT / f"{coin}_1h.parquet", index=False)
        print(f"{coin:9s} {len(df):6d} hourly candles, {pd.to_datetime(df.ts.min(), unit='s')} to {pd.to_datetime(df.ts.max(), unit='s')}")
    for currency in ("BTC", "ETH"):
        df = dvol(currency, start_ms, end_ms)
        df.to_parquet(OUT / f"dvol_{currency}.parquet", index=False)
        print(f"DVOL {currency}: {len(df):6d} hourly points, {pd.to_datetime(df.ts.min(), unit='s')} to "
              f"{pd.to_datetime(df.ts.max(), unit='s')}, last {df.close.iloc[-1]:.1f}")


if __name__ == "__main__":
    main()

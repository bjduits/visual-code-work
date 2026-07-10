#!/usr/bin/env python3
"""
Market scanner: discover "hot or not" crypto and stocks beyond the fixed
CRYPTO_FOCUS / STOCK_FOCUS watchlist.

This script:
1. Fetches crypto trending coins and top 24h gainers/losers from CoinGecko
   (top 100 by market cap, not limited to CRYPTO_FOCUS)
2. Fetches stock day gainers, day losers, and most-active tickers from
   Yahoo Finance's screener (not limited to STOCK_FOCUS)
3. Scores and labels momentum/risk using the same logic as
   gather_trading_research.py
4. Writes a discovery report to .tmp/

This is a research tool only. It is not financial advice. Results are NOT
filtered by platform availability -- verify any asset is actually tradeable
on your platform (Coinmerce for crypto, Degiro.nl for stocks) before acting
on it.
"""

import os
import sys
import json
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

from dotenv import load_dotenv

from gather_trading_research import (
    YAHOO_HEADERS,
    analyze_crypto,
    analyze_stock,
    fetch_stock_history,
    load_positions,
    tmp_dir,
)

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(tmp_dir / "market_scanner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CRYPTO_PLATFORM = os.getenv("CRYPTO_PLATFORM", "Coinmerce")
STOCK_PLATFORM = os.getenv("STOCK_PLATFORM", "Degiro.nl")


def fetch_crypto_universe(per_page: int = 100) -> List[Dict]:
    import requests

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": 1,
        "price_change_percentage": "24h,7d",
        "sparkline": "false",
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    logger.info(f"Fetched crypto universe of {len(data)} assets")
    return data


def fetch_crypto_trending() -> List[str]:
    import requests

    url = "https://api.coingecko.com/api/v3/search/trending"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    coins = response.json().get("coins", [])
    ids = [c["item"]["id"] for c in coins if c.get("item", {}).get("id")]
    logger.info(f"Fetched {len(ids)} trending crypto ids")
    return ids


def fetch_crypto_markets_by_id(coin_ids: List[str]) -> List[Dict]:
    import requests

    if not coin_ids:
        return []

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
        "order": "market_cap_desc",
        "per_page": len(coin_ids),
        "price_change_percentage": "24h,7d",
        "sparkline": "false",
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def scan_crypto(positions: Dict[str, Dict], top_n: int = 10) -> Dict[str, List[Dict]]:
    universe = fetch_crypto_universe(per_page=100)
    universe_ids = {asset["id"] for asset in universe}

    trending_ids = fetch_crypto_trending()
    missing_trending_ids = [cid for cid in trending_ids if cid not in universe_ids]
    trending_extra = fetch_crypto_markets_by_id(missing_trending_ids) if missing_trending_ids else []

    by_id = {asset["id"]: asset for asset in universe}
    by_id.update({asset["id"]: asset for asset in trending_extra})

    gainers = sorted(
        universe, key=lambda a: a.get("price_change_percentage_24h_in_currency") or 0.0, reverse=True
    )[:top_n]
    losers = sorted(
        universe, key=lambda a: a.get("price_change_percentage_24h_in_currency") or 0.0
    )[:top_n]
    trending = [by_id[cid] for cid in trending_ids if cid in by_id][:top_n]

    def analyze_all(assets: List[Dict]) -> List[Dict]:
        results = []
        for asset in assets:
            entry = analyze_crypto(asset, positions)
            entry["platform"] = CRYPTO_PLATFORM
            results.append(entry)
        return results

    return {
        "trending": analyze_all(trending),
        "top_gainers_24h": analyze_all(gainers),
        "top_losers_24h": analyze_all(losers),
    }


def fetch_stock_screener(screen_id: str, count: int = 10) -> List[Dict]:
    import requests

    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    params = {
        "formatted": "false",
        "lang": "en-US",
        "region": "US",
        "scrIds": screen_id,
        "count": count,
    }
    response = requests.get(url, params=params, headers=YAHOO_HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()
    results = data.get("finance", {}).get("result", [])
    quotes = results[0].get("quotes", []) if results else []
    logger.info(f"Fetched {len(quotes)} quotes for screener '{screen_id}'")
    return quotes


def quote_to_asset(quote: Dict) -> Dict:
    symbol = quote.get("symbol", "")
    try:
        history = fetch_stock_history(symbol)
    except Exception as exc:
        logger.warning(f"Could not fetch history for {symbol}: {exc}")
        history = {}

    return {
        "symbol": symbol,
        "longName": quote.get("longName") or quote.get("shortName"),
        "regularMarketPrice": quote.get("regularMarketPrice"),
        "regularMarketChangePercent": quote.get("regularMarketChangePercent"),
        "regularMarketVolume": quote.get("regularMarketVolume"),
        "marketCap": quote.get("marketCap"),
        "price_history": history,
    }


def scan_stocks(positions: Dict[str, Dict], count: int = 10) -> Dict[str, List[Dict]]:
    screens = {
        "day_gainers": "top_gainers",
        "day_losers": "top_losers",
        "most_actives": "most_active",
    }

    output: Dict[str, List[Dict]] = {}
    for scr_id, label in screens.items():
        try:
            quotes = fetch_stock_screener(scr_id, count=count)
        except Exception as exc:
            logger.error(f"Stock screener '{scr_id}' failed: {exc}")
            output[label] = []
            continue

        results = []
        for quote in quotes:
            asset = quote_to_asset(quote)
            if asset.get("regularMarketPrice") is None:
                continue
            entry = analyze_stock(asset, positions)
            entry["platform"] = STOCK_PLATFORM
            results.append(entry)
        output[label] = results

    return output


def build_summary(crypto_scan: Dict[str, List[Dict]], stock_scan: Dict[str, List[Dict]]) -> str:
    lines = [
        f"Market Scanner Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "This is an unfiltered market discovery scan, NOT limited to CRYPTO_FOCUS/STOCK_FOCUS.",
        "Verify liquidity, fees, and actual platform availability before acting on anything here.",
        "This is not financial advice.",
        "",
    ]

    def crypto_lines(title: str, assets: List[Dict]) -> List[str]:
        out = [title]
        if not assets:
            out.append("- No data")
        for asset in assets:
            held_label = " (HELD)" if asset.get("held") else ""
            out.append(
                f"- {asset['name']} ({asset['symbol'].upper()}){held_label} [{asset.get('platform', 'n/a')}]: "
                f"${asset['current_price']} | 24h: {asset['change_24h_pct']}% | 7d: {asset['change_7d_pct']}% | "
                f"momentum: {asset['momentum']} | risk: {asset['risk_level']} | score: {asset['score']}"
            )
        out.append("")
        return out

    def stock_lines(title: str, assets: List[Dict]) -> List[str]:
        out = [title]
        if not assets:
            out.append("- No data")
        for asset in assets:
            held_label = " (HELD)" if asset.get("held") else ""
            out.append(
                f"- {asset['symbol'].upper()} ({asset['name']}){held_label} [{asset.get('platform', 'n/a')}]: "
                f"${asset['current_price']} | 1d: {asset['change_pct']}% | 7d: {asset['change_7d_pct']}% | "
                f"momentum: {asset['momentum']} | risk: {asset['risk_level']} | score: {asset['score']}"
            )
        out.append("")
        return out

    lines += crypto_lines("Crypto - Trending (search interest):", crypto_scan.get("trending", []))
    lines += crypto_lines("Crypto - Top Gainers (24h, HOT):", crypto_scan.get("top_gainers_24h", []))
    lines += crypto_lines("Crypto - Top Losers (24h, NOT):", crypto_scan.get("top_losers_24h", []))
    lines += stock_lines("Stocks - Day Gainers (HOT):", stock_scan.get("top_gainers", []))
    lines += stock_lines("Stocks - Day Losers (NOT):", stock_scan.get("top_losers", []))
    lines += stock_lines("Stocks - Most Active (high interest, direction unclear):", stock_scan.get("most_active", []))

    return "\n".join(lines)


def save_report(report: Dict, summary_text: str) -> None:
    report_path = tmp_dir / "market_scanner_report.json"
    summary_path = tmp_dir / "market_scanner_summary.txt"

    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write(summary_text)

    logger.info(f"Report saved to {report_path}")
    logger.info(f"Summary saved to {summary_path}")


def main():
    try:
        import requests  # type: ignore
    except ImportError:
        logger.error("The 'requests' package is required. Install it with: python -m pip install requests")
        sys.exit(1)

    positions = load_positions()

    crypto_scan: Dict[str, List[Dict]] = {}
    try:
        crypto_scan = scan_crypto(positions)
    except Exception as exc:
        logger.error(f"Crypto scan failed: {exc}")

    stock_scan: Dict[str, List[Dict]] = {}
    try:
        stock_scan = scan_stocks(positions)
    except Exception as exc:
        logger.error(f"Stock scan failed: {exc}")

    summary = build_summary(crypto_scan, stock_scan)
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "crypto_scan": crypto_scan,
        "stock_scan": stock_scan,
    }
    save_report(report, summary)

    print(summary)


if __name__ == "__main__":
    main()

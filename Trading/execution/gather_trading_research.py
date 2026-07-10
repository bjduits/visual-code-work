#!/usr/bin/env python3
"""
Gather short-term trading research data for crypto and small-cap stocks.

This script:
1. Loads asset lists from .env
2. Fetches crypto market data from CoinGecko
3. Fetches stock quote data from Yahoo Finance
4. Optionally fetches market headlines from NewsAPI
5. Calculates short-term momentum and volatility signals
6. Writes a report to .tmp/

This is a research tool only. It is not financial advice.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Setup directories
root_dir = Path(__file__).parent.parent
tmp_dir = root_dir / ".tmp"
tmp_dir.mkdir(exist_ok=True)
script_dir = Path(__file__).parent
POSITIONS_PATH = script_dir / "positions.json"
FALLBACK_POSITIONS_PATH = tmp_dir / "positions.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(tmp_dir / "trading_research.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def fetch_crypto_data(coin_ids: List[str]) -> List[Dict]:
    import requests

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(coin_ids),
        "order": "market_cap_desc",
        "per_page": len(coin_ids) or 100,
        "price_change_percentage": "24h,7d",
        "sparkline": "false"
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    logger.info(f"Fetched crypto market data for {len(data)} assets")
    return data


YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def fetch_stock_history(symbol: str) -> Dict:
    import requests

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        "range": "7d",
        "interval": "1d",
        "includePrePost": "false",
    }

    response = requests.get(url, params=params, headers=YAHOO_HEADERS, timeout=15)
    response.raise_for_status()
    return response.json()


def fetch_stock_data(symbols: List[str]) -> List[Dict]:
    if not symbols:
        return []

    # Yahoo's v7/finance/quote endpoint now requires an auth crumb and returns
    # 401 for unauthenticated requests, so quote data is derived from the
    # v8/finance/chart endpoint's `meta` block instead, which still works.
    enriched_quotes = []
    for symbol in symbols:
        try:
            history = fetch_stock_history(symbol)
        except Exception as exc:
            logger.warning(f"Could not fetch data for {symbol}: {exc}")
            continue

        meta = history.get("chart", {}).get("result", [{}])[0].get("meta", {})
        current_price = meta.get("regularMarketPrice")
        previous_close = meta.get("chartPreviousClose") or meta.get("previousClose")
        change_pct = None
        if current_price is not None and previous_close:
            change_pct = (current_price - previous_close) / previous_close * 100.0

        quote = {
            "symbol": meta.get("symbol", symbol),
            "longName": meta.get("longName"),
            "shortName": meta.get("shortName"),
            "regularMarketPrice": current_price,
            "regularMarketChangePercent": change_pct,
            "regularMarketVolume": meta.get("regularMarketVolume"),
            "marketCap": meta.get("marketCap"),
            "price_history": history,
        }
        enriched_quotes.append(quote)

    logger.info(f"Fetched stock quote data for {len(enriched_quotes)} assets")
    return enriched_quotes


def load_positions() -> Dict[str, Dict]:
    positions: Dict[str, Dict] = {}
    if POSITIONS_PATH.exists():
        try:
            with open(POSITIONS_PATH, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
                for symbol, info in raw.items():
                    positions[str(symbol).upper()] = info
        except Exception as exc:
            logger.warning(f"Could not load positions from {POSITIONS_PATH}: {exc}")
    elif FALLBACK_POSITIONS_PATH.exists():
        try:
            with open(FALLBACK_POSITIONS_PATH, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
                for symbol, info in raw.items():
                    positions[str(symbol).upper()] = info
        except Exception as exc:
            logger.warning(f"Could not load positions from {FALLBACK_POSITIONS_PATH}: {exc}")

    current_positions = os.getenv("CURRENT_POSITIONS", "").strip()
    if current_positions:
        for item in current_positions.split(","):
            parts = [part.strip() for part in item.split(":") if part.strip()]
            if len(parts) >= 2:
                symbol = parts[0].upper()
                try:
                    avg_price = float(parts[1])
                except ValueError:
                    continue
                position = {"avg_price": avg_price}
                if len(parts) >= 3:
                    try:
                        position["quantity"] = float(parts[2])
                    except ValueError:
                        pass
                positions[symbol] = position

    return positions


def compute_sell_signal(held: bool, unrealized_pct: Optional[float], momentum: str, risk_level: str, volatility: str) -> str:
    if not held:
        return "Not held"
    if unrealized_pct is None:
        return "Hold and monitor"

    if unrealized_pct >= 20 and momentum.startswith("strong"):
        return "Recommend taking profit"
    if unrealized_pct >= 12 and momentum.startswith("moderate"):
        return "Consider partial profit taking"
    if unrealized_pct <= -6 and (risk_level == "high" or volatility == "high"):
        return "Consider cutting losses"
    if unrealized_pct <= -8:
        return "Review position; possible stop-loss"
    if momentum.startswith("strong downtrend"):
        return "Consider selling to protect capital"
    return "Hold and monitor"


def evaluate_holdings(symbol: str, current_price: Optional[float], positions: Dict[str, Dict], momentum: str, risk_level: str, volatility: str) -> Dict:
    symbol_key = str(symbol).upper()
    position = positions.get(symbol_key)
    held = bool(position and current_price is not None)
    avg_price = position.get("avg_price") if position else None
    quantity = position.get("quantity") if position else None
    unrealized_pct = None
    if held and avg_price and current_price:
        try:
            unrealized_pct = round((current_price - avg_price) / avg_price * 100.0, 2)
        except Exception:
            unrealized_pct = None
    sell_signal = compute_sell_signal(held, unrealized_pct, momentum, risk_level, volatility)
    return {
        "held": held,
        "avg_price": avg_price,
        "quantity": quantity,
        "unrealized_pct": unrealized_pct,
        "sell_signal": sell_signal,
    }


def fetch_market_news(query: str, api_key: Optional[str]) -> List[Dict]:
    if not api_key:
        logger.info("Skipping NewsAPI news fetch (no key configured)")
        return []

    import requests

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": api_key,
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    articles = data.get("articles", [])
    logger.info(f"Fetched {len(articles)} news articles for query: {query}")
    return articles


def score_crypto(change_24h: float, change_7d: float, volume: float) -> int:
    score = 50
    score += int(min(max(change_24h, -10.0), 10.0) * 2)
    score += int(min(max(change_7d, -20.0), 20.0))
    score += 1 if volume > 50_000_000 else 0
    score = max(0, min(100, score))
    return score


def analyze_crypto(asset: Dict, positions: Dict[str, Dict]) -> Dict:
    current = asset.get("current_price")
    change_24h = asset.get("price_change_percentage_24h_in_currency") or 0.0
    change_7d = asset.get("price_change_percentage_7d_in_currency") or 0.0
    market_cap = asset.get("market_cap") or 0
    volume = asset.get("total_volume") or 0

    momentum = "neutral"
    if change_7d > 10 and change_24h > 2:
        momentum = "strong uptrend"
    elif change_7d > 3 and change_24h > 0:
        momentum = "moderate uptrend"
    elif change_7d < -10 and change_24h < -2:
        momentum = "strong downtrend"
    elif change_7d < -3 and change_24h < 0:
        momentum = "moderate downtrend"

    volatility = "low"
    if abs(change_24h) > 10 or abs(change_7d) > 20:
        volatility = "high"
    elif abs(change_24h) > 5 or abs(change_7d) > 10:
        volatility = "medium"

    risk_level = "low"
    if volatility == "high" or change_7d < -8:
        risk_level = "high"
    elif volatility == "medium" or abs(change_7d) > 7:
        risk_level = "medium"

    long_term_note = "watch for trend confirmation"
    if market_cap > 10_000_000_000 and change_7d > 7:
        long_term_note = "positive long-term potential"
    elif change_7d < -12:
        long_term_note = "high long-term risk"

    estimated_cost_pct = 0.18
    estimated_profit_pct = min(max((change_7d + change_24h) / 2, -15.0), 25.0)
    score = score_crypto(change_24h, change_7d, volume)
    hold_info = evaluate_holdings(asset.get("symbol", ""), current, positions, momentum, risk_level, volatility)

    return {
        "symbol": asset.get("symbol", ""),
        "name": asset.get("name", ""),
        "current_price": current,
        "market_cap": market_cap,
        "volume": volume,
        "change_24h_pct": round(change_24h, 2),
        "change_7d_pct": round(change_7d, 2),
        "momentum": momentum,
        "volatility": volatility,
        "risk_level": risk_level,
        "long_term_note": long_term_note,
        "estimated_cost_pct": round(estimated_cost_pct, 2),
        "estimated_profit_pct": round(estimated_profit_pct, 2),
        "score": score,
        "source": "CoinGecko",
        "platform": os.getenv("CRYPTO_PLATFORM", "Coinmerce"),
        **hold_info
    }


def compute_stock_7d_change(asset: Dict) -> float:
    history = asset.get("price_history", {})
    result = history.get("chart", {}).get("result")
    if not result:
        return 0.0

    quote_data = result[0].get("indicators", {}).get("quote", [])
    if not quote_data or not quote_data[0].get("close"):
        return 0.0

    closes = [price for price in quote_data[0]["close"] if price is not None]
    if len(closes) < 2:
        return 0.0

    return ((closes[-1] - closes[0]) / closes[0]) * 100.0 if closes[0] else 0.0


def score_stock(asset: Dict) -> int:
    score = 50
    change_pct = asset.get("change_pct", 0.0)
    change_7d = asset.get("change_7d_pct", 0.0)
    volume = asset.get("volume", 0)

    score += int(min(max(change_pct, -10.0), 10.0) * 2)
    score += int(min(max(change_7d, -20.0), 20.0))
    score += 1 if volume > 5_000_000 else 0
    score = max(0, min(100, score))
    return score


def analyze_stock(asset: Dict, positions: Dict[str, Dict]) -> Dict:
    current = asset.get("regularMarketPrice")
    change_pct = asset.get("regularMarketChangePercent") or 0.0
    change_7d = compute_stock_7d_change(asset)
    market_cap = asset.get("marketCap") or 0
    volume = asset.get("regularMarketVolume") or 0

    momentum = "neutral"
    if change_pct > 5 and change_7d > 5:
        momentum = "strong short-term bullish"
    elif change_pct > 2 and change_7d > 0:
        momentum = "moderate bullish"
    elif change_pct < -5 and change_7d < -3:
        momentum = "strong bearish"
    elif change_pct < -2 and change_7d < 0:
        momentum = "moderate bearish"

    volatility = "low"
    if abs(change_pct) > 8 or abs(change_7d) > 12:
        volatility = "high"
    elif abs(change_pct) > 4 or abs(change_7d) > 6:
        volatility = "medium"

    score = score_stock({
        "change_pct": change_pct,
        "change_7d_pct": change_7d,
        "volume": volume,
    })

    risk_level = "low"
    if volatility == "high" or change_7d < -8:
        risk_level = "high"
    elif volatility == "medium" or abs(change_7d) > 7:
        risk_level = "medium"

    long_term_note = "watch for trend confirmation"
    if market_cap > 5_000_000_000 and change_7d > 4:
        long_term_note = "positive long-term potential"
    elif change_7d < -10:
        long_term_note = "high long-term risk"

    estimated_cost_pct = 0.25
    estimated_profit_pct = min(max((change_pct + change_7d) / 2, -15.0), 20.0)

    hold_info = evaluate_holdings(asset.get("symbol", ""), current, positions, momentum, risk_level, volatility)

    return {
        "symbol": asset.get("symbol", ""),
        "name": asset.get("longName") or asset.get("shortName") or asset.get("symbol"),
        "current_price": current,
        "market_cap": market_cap,
        "volume": volume,
        "change_pct": round(change_pct, 2),
        "change_7d_pct": round(change_7d, 2),
        "momentum": momentum,
        "volatility": volatility,
        "risk_level": risk_level,
        "long_term_note": long_term_note,
        "estimated_cost_pct": round(estimated_cost_pct, 2),
        "estimated_profit_pct": round(estimated_profit_pct, 2),
        "score": score,
        "source": "Yahoo Finance",
        "platform": os.getenv("STOCK_PLATFORM", "Degiro.nl"),
        **hold_info
    }


def build_summary(crypto_analysis: List[Dict], stock_analysis: List[Dict], news: List[Dict]) -> str:
    lines = [
        f"Trading Research Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Top Crypto Candidates:",
    ]

    for asset in sorted(crypto_analysis, key=lambda x: x.get("score", 0), reverse=True)[:7]:
        lines.append(
            f"- {asset['name']} ({asset['symbol'].upper()}): ${asset['current_price']} | 24h: {asset['change_24h_pct']}% | 7d: {asset['change_7d_pct']}% | risk: {asset.get('risk_level', 'n/a')} | {asset['momentum']} | score: {asset['score']} | est profit: {asset.get('estimated_profit_pct', 0)}% | platform: {asset.get('platform', 'n/a')}"
        )

    lines.append("")
    lines.append("Top Stock Candidates:")
    for asset in sorted(stock_analysis, key=lambda x: x.get("score", 0), reverse=True)[:7]:
        lines.append(
            f"- {asset['symbol'].upper()} ({asset['name']}): ${asset['current_price']} | 1d: {asset['change_pct']}% | 7d: {asset['change_7d_pct']}% | risk: {asset.get('risk_level', 'n/a')} | {asset['momentum']} | score: {asset['score']} | est profit: {asset.get('estimated_profit_pct', 0)}% | platform: {asset.get('platform', 'n/a')}"
        )

    lines.append("")
    lines.append("Key News Headlines:")
    if news:
        for article in news[:5]:
            published = article.get("publishedAt", "")
            title = article.get("title", "")
            source = article.get("source", {}).get("name", "")
            lines.append(f"- [{source}] {title} ({published})")
    else:
        lines.append("- No news fetched or NEWSAPI_KEY not configured.")

    lines.append("")
    lines.append("Notes:")
    lines.append("- Use this report as a short-term research guide, not a trade signal.")
    lines.append("- Review liquidity, spreads, and your own risk limits before taking any position.")
    lines.append("- Refine the asset lists in .env to match your preferred universe.")

    return "\n".join(lines)


def save_report(report: Dict, summary_text: str) -> None:
    report_path = tmp_dir / "trading_research_report.json"
    summary_path = tmp_dir / "trading_research_summary.txt"

    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write(summary_text)

    logger.info(f"Report saved to {report_path}")
    logger.info(f"Summary saved to {summary_path}")


def load_asset_list(env_key: str, default: str) -> List[str]:
    raw = os.getenv(env_key, default)
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def main():
    try:
        import requests  # type: ignore
    except ImportError:
        logger.error("The 'requests' package is required. Install it with: python -m pip install requests")
        sys.exit(1)

    crypto_focus = load_asset_list("CRYPTO_FOCUS", "bitcoin,ethereum,solana,chainlink,polkadot")
    stock_focus = load_asset_list("STOCK_FOCUS", "GME,AMC,PLTR,SOFI,BB,CLNE,SPCE")
    newsapi_key = os.getenv("NEWSAPI_KEY", "")

    if not crypto_focus and not stock_focus:
        logger.error("No assets configured in CRYPTO_FOCUS or STOCK_FOCUS")
        sys.exit(1)

    crypto_results: List[Dict] = []
    stock_results: List[Dict] = []
    news_results: List[Dict] = []

    positions = load_positions()

    if crypto_focus:
        try:
            crypto_assets = fetch_crypto_data(crypto_focus)
            crypto_results = [analyze_crypto(asset, positions) for asset in crypto_assets]
        except Exception as exc:
            logger.error(f"Crypto data fetch failed: {exc}")

    if stock_focus:
        try:
            stock_assets = fetch_stock_data([symbol.upper() for symbol in stock_focus])
            stock_results = [analyze_stock(asset, positions) for asset in stock_assets if asset.get("regularMarketPrice") is not None]
        except Exception as exc:
            logger.error(f"Stock data fetch failed: {exc}")

    if newsapi_key:
        try:
            news_results = fetch_market_news("crypto OR small cap stock", newsapi_key)
        except Exception as exc:
            logger.error(f"News fetch failed: {exc}")

    summary = build_summary(crypto_results, stock_results, news_results)
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "crypto_analysis": crypto_results,
        "stock_analysis": stock_results,
        "news": news_results,
    }
    save_report(report, summary)

    print(summary)


if __name__ == "__main__":
    main()

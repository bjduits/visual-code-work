#!/usr/bin/env python3
"""
External market-context signals that are independent of an asset's own recent
price action -- used to sanity-check (not replace) the momentum scoring in
gather_trading_research.py.

Why this exists: pure momentum scoring rewards an asset for having *already*
moved, which means it tends to flag assets right as they get crowded/late in
a move. These signals add outside information (crowd sentiment, leverage
positioning, market-wide fear, and independent analyst opinion) so the score
can be pulled back down when a "hot" asset looks crowded or over-extended,
instead of only ever pushing scores up on recent price change.

None of these require an API key:
- Fear & Greed Index: alternative.me (free, public)
- Crypto funding rates: Binance USDT-margined futures (free, public)
- VIX: Yahoo Finance chart endpoint (same unauthenticated endpoint already
  used elsewhere in this project)
- Analyst recommendation trend / price target: Yahoo quoteSummary endpoint
  (same class of unofficial endpoint already used elsewhere here -- like the
  others, it can occasionally 401/change shape without notice, so every
  function here fails soft: log a warning and return None)

Every function here is best-effort: on any failure it logs a warning and
returns None so callers can carry on without this signal, matching the
fail-soft pattern used throughout gather_trading_research.py.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

FEAR_GREED_URL = "https://api.alternative.me/fng/"
BINANCE_FUNDING_URL = "https://fapi.binance.com/fapi/v1/premiumIndex"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
YAHOO_QUOTE_SUMMARY_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
YAHOO_CRUMB_COOKIE_URL = "https://fc.yahoo.com"
YAHOO_CRUMB_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"

# The quoteSummary endpoint (unlike the v8/chart endpoint used elsewhere in
# this project) requires a session cookie + crumb since Yahoo tightened
# unauthenticated access. This session/crumb are fetched once and reused for
# every ticker in a run rather than re-negotiated per symbol.
_yahoo_session = None
_yahoo_crumb = None


def _get_yahoo_crumb(yahoo_headers: Dict[str, str]):
    """Returns (session, crumb) for authenticated Yahoo quoteSummary calls.

    Best-effort: returns (session, None) if the crumb can't be obtained, in
    which case callers should skip the quoteSummary request rather than call
    it without a crumb (that reliably 401s).
    """
    import requests

    global _yahoo_session, _yahoo_crumb
    if _yahoo_session is not None:
        return _yahoo_session, _yahoo_crumb

    session = requests.Session()
    session.headers.update(yahoo_headers)
    try:
        # Establishes the session cookie Yahoo expects before issuing a crumb.
        session.get(YAHOO_CRUMB_COOKIE_URL, timeout=15)
        response = session.get(YAHOO_CRUMB_URL, timeout=15)
        response.raise_for_status()
        crumb = response.text.strip()
        _yahoo_session, _yahoo_crumb = session, (crumb or None)
    except Exception as exc:
        logger.warning(f"Could not obtain Yahoo crumb (analyst signal will be skipped): {exc}")
        _yahoo_session, _yahoo_crumb = session, None

    return _yahoo_session, _yahoo_crumb

# CoinGecko id -> Binance USDT-margined perpetual symbol, for the common
# CRYPTO_FOCUS entries. Anything not listed here falls back to
# f"{TICKER}USDT" (see binance_symbol_for), which covers most major coins.
COINGECKO_TO_BINANCE = {
    "bitcoin": "BTCUSDT",
    "ethereum": "ETHUSDT",
    "solana": "SOLUSDT",
    "chainlink": "LINKUSDT",
    "polkadot": "DOTUSDT",
    "cardano": "ADAUSDT",
    "dogecoin": "DOGEUSDT",
    "ripple": "XRPUSDT",
    "litecoin": "LTCUSDT",
    "avalanche-2": "AVAXUSDT",
    "polygon": "MATICUSDT",
    "matic-network": "MATICUSDT",
    "binancecoin": "BNBUSDT",
}


def binance_symbol_for(coingecko_id: str, ticker_symbol: str) -> Optional[str]:
    mapped = COINGECKO_TO_BINANCE.get((coingecko_id or "").lower())
    if mapped:
        return mapped
    if ticker_symbol:
        return f"{ticker_symbol.upper()}USDT"
    return None


def fetch_fear_greed_index() -> Optional[Dict]:
    """Crypto-wide Fear & Greed Index, 0 (extreme fear) - 100 (extreme greed)."""
    import requests

    try:
        response = requests.get(FEAR_GREED_URL, params={"limit": 1, "format": "json"}, timeout=15)
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            return None
        entry = data[0]
        return {
            "value": int(entry["value"]),
            "classification": entry.get("value_classification", ""),
        }
    except Exception as exc:
        logger.warning(f"Could not fetch Fear & Greed index: {exc}")
        return None


def fetch_funding_rate(binance_symbol: str) -> Optional[float]:
    """Latest perpetual futures funding rate for `binance_symbol`, as a % per 8h.

    Positive = longs pay shorts (crowd is leveraged long -> squeeze-down risk).
    Negative = shorts pay longs (crowd is leveraged short -> squeeze-up risk).
    """
    import requests

    if not binance_symbol:
        return None
    try:
        response = requests.get(BINANCE_FUNDING_URL, params={"symbol": binance_symbol}, timeout=15)
        response.raise_for_status()
        rate = response.json().get("lastFundingRate")
        return round(float(rate) * 100.0, 4) if rate is not None else None
    except Exception as exc:
        logger.warning(f"Could not fetch funding rate for {binance_symbol}: {exc}")
        return None


def fetch_vix(yahoo_headers: Dict[str, str]) -> Optional[Dict]:
    """Current CBOE VIX level and its change vs previous close."""
    import requests

    try:
        response = requests.get(
            YAHOO_CHART_URL, params={"range": "5d", "interval": "1d"}, headers=yahoo_headers, timeout=15
        )
        response.raise_for_status()
        meta = response.json().get("chart", {}).get("result", [{}])[0].get("meta", {})
        current = meta.get("regularMarketPrice")
        previous = meta.get("chartPreviousClose") or meta.get("previousClose")
        change_pct = None
        if current is not None and previous:
            change_pct = round((current - previous) / previous * 100.0, 2)
        if current is None:
            return None
        return {"value": round(current, 2), "change_pct": change_pct}
    except Exception as exc:
        logger.warning(f"Could not fetch VIX: {exc}")
        return None


def _raw(node: Optional[Dict]) -> Optional[float]:
    if isinstance(node, dict):
        return node.get("raw")
    return None


def fetch_analyst_signal(symbol: str, yahoo_headers: Dict[str, str]) -> Optional[Dict]:
    """Analyst recommendation consensus and price target for a stock ticker.

    This is independent of recent price action (it reflects analysts'
    fundamental view), so it's useful for catching divergence: an asset with
    strong recent momentum but a bearish/skeptical analyst consensus is a
    different (weaker) setup than one where both agree.
    """
    session, crumb = _get_yahoo_crumb(yahoo_headers)
    if not crumb:
        return None

    try:
        url = YAHOO_QUOTE_SUMMARY_URL.format(symbol=symbol)
        params = {"modules": "recommendationTrend,financialData", "crumb": crumb}
        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        results = response.json().get("quoteSummary", {}).get("result") or []
        if not results:
            return None
        node = results[0]

        trend_list = node.get("recommendationTrend", {}).get("trend", [])
        current_trend = trend_list[0] if trend_list else {}

        financial = node.get("financialData", {})
        target_mean = _raw(financial.get("targetMeanPrice"))
        recommendation_mean = _raw(financial.get("recommendationMean"))
        current_price = _raw(financial.get("currentPrice"))

        upside_pct = None
        if target_mean and current_price:
            upside_pct = round((target_mean - current_price) / current_price * 100.0, 2)

        return {
            "strong_buy": current_trend.get("strongBuy"),
            "buy": current_trend.get("buy"),
            "hold": current_trend.get("hold"),
            "sell": current_trend.get("sell"),
            "strong_sell": current_trend.get("strongSell"),
            "recommendation_mean": recommendation_mean,  # 1.0 = Strong Buy ... 5.0 = Sell
            "target_mean_price": target_mean,
            "target_upside_pct": upside_pct,
        }
    except Exception as exc:
        logger.warning(f"Could not fetch analyst signal for {symbol}: {exc}")
        return None


def apply_crypto_context(
    score: int,
    risk_level: str,
    change_7d: float,
    fear_greed: Optional[Dict],
    funding_rate_pct: Optional[float],
) -> (int, str, List[str]):
    """Adjust a momentum score/risk level using sentiment + positioning data.

    Deliberately asymmetric: these signals only ever *penalize* already-hot
    assets (crowded sentiment, over-leveraged longs) rather than adding to an
    already-positive momentum score, since the momentum score is already
    biased toward chasing recent moves.
    """
    notes: List[str] = []

    if fear_greed:
        value = fear_greed["value"]
        if value >= 75 and change_7d > 5:
            score -= 8
            if risk_level == "low":
                risk_level = "medium"
            notes.append(
                f"Fear & Greed {value} (extreme greed) while already up {change_7d:.1f}% over 7d: "
                "crowded / late-stage move, squeeze-down risk."
            )
        elif value <= 20:
            notes.append(
                f"Fear & Greed {value} (extreme fear): broad market pessimism -- don't fight a "
                "confirmed downtrend, but watch for contrarian setups forming."
            )

    if funding_rate_pct is not None:
        if funding_rate_pct > 0.05:
            score -= 6
            risk_level = "high"
            notes.append(
                f"Funding rate {funding_rate_pct:+.3f}%/8h: longs paying heavily, positioning is "
                "over-leveraged long -- squeeze-down risk."
            )
        elif funding_rate_pct < -0.03:
            notes.append(
                f"Funding rate {funding_rate_pct:+.3f}%/8h: shorts paying longs -- crowd is leveraged "
                "short, potential short-squeeze upside."
            )

    score = max(0, min(100, score))
    return score, risk_level, notes


def apply_stock_context(
    score: int,
    risk_level: str,
    vix: Optional[Dict],
    analyst: Optional[Dict],
) -> (int, str, List[str]):
    """Adjust a momentum score/risk level using macro backdrop + analyst view."""
    notes: List[str] = []

    if vix and vix.get("value") is not None:
        value = vix["value"]
        if value >= 25:
            score -= 5
            if risk_level == "low":
                risk_level = "medium"
            notes.append(f"VIX {value:.1f}: elevated market-wide fear, risk-off backdrop for equities.")
        elif value <= 14:
            notes.append(f"VIX {value:.1f}: low volatility / complacent backdrop.")

    if analyst:
        rec_mean = analyst.get("recommendation_mean")
        upside = analyst.get("target_upside_pct")
        if rec_mean is not None:
            if rec_mean <= 2.0:
                score += 6
                notes.append(f"Analyst consensus bullish (mean rating {rec_mean:.1f}/5).")
            elif rec_mean >= 3.5:
                score -= 6
                notes.append(
                    f"Analyst consensus bearish (mean rating {rec_mean:.1f}/5) despite recent price "
                    "action -- divergence warning."
                )
        if upside is not None and upside < -5:
            notes.append(
                f"Price is already {abs(upside):.1f}% above the average analyst target -- limited "
                "fundamental upside left by that measure."
            )

    score = max(0, min(100, score))
    return score, risk_level, notes

#!/usr/bin/env python3
"""
AI Trading Advisor Agent

This script generates a research-backed advisor summary for short-term and long-term trading.
It uses the research report output and optionally writes records into Airtable.

This is not a live trading execution script.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

root_dir = Path(__file__).parent.parent
tmp_dir = root_dir / ".tmp"
tmp_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(tmp_dir / "trading_advisor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

AI_ADVICE_PROMPT = (
    "You are a trading research advisor. Given asset performance data with short-term and long-term signals, "
    "produce a concise summary with recommendations for short-term (week), long-term (6 months), risk, cost estimates, "
    "and expected profit percentage. Use a neutral tone and do not provide live trade execution."
)

AIRTABLE_ENABLED = os.getenv("TRADING_ADVISOR_USE_AIRTABLE", "0") == "1"
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "TradingAdvice")

USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "0") == "1"
GPT4ALL_MODEL_PATH = os.getenv("GPT4ALL_MODEL_PATH", "")

REPORT_PATH = tmp_dir / "trading_research_report.json"
SUMMARY_PATH = tmp_dir / "trading_advisor_summary.txt"
OUTPUT_PATH = tmp_dir / "trading_advisor_output.json"


def load_report() -> Dict:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Research report not found: {REPORT_PATH}")
    with open(REPORT_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


SELL_SIGNAL_TO_ADVICE = {
    "Recommend taking profit": "Sell",
    "Consider partial profit taking": "Sell partial",
    "Consider cutting losses": "Sell",
    "Review position; possible stop-loss": "Sell",
    "Consider selling to protect capital": "Sell",
    "Hold and monitor": "Hold",
}


def compute_advice(held: bool, sell_signal: str, score: int) -> str:
    if held:
        return SELL_SIGNAL_TO_ADVICE.get(sell_signal, "Hold")
    if score >= 65:
        return "Buy"
    if score >= 55:
        return "Watch"
    return "Avoid"


# --- Dutch translations applied only to the values written to Airtable;
# column names and internal logic keep using the English source strings. ---
MOMENTUM_NL = {
    "neutral": "neutraal",
    "strong uptrend": "sterk stijgend",
    "moderate uptrend": "gematigd stijgend",
    "strong downtrend": "sterk dalend",
    "moderate downtrend": "gematigd dalend",
    "strong short-term bullish": "sterk bullish (korte termijn)",
    "moderate bullish": "gematigd bullish",
    "strong bearish": "sterk bearish",
    "moderate bearish": "gematigd bearish",
}
LONG_TERM_NOTE_NL = {
    "watch for trend confirmation": "wacht op trendbevestiging",
    "positive long-term potential": "positief potentieel op lange termijn",
    "high long-term risk": "hoog risico op lange termijn",
    "unclear": "onduidelijk",
}
RISK_NL = {"low": "laag", "medium": "gemiddeld", "high": "hoog"}
ADVICE_NL = {
    "Buy": "Kopen",
    "Watch": "Volgen",
    "Avoid": "Vermijden",
    "Sell": "Verkopen",
    "Sell partial": "Gedeeltelijk verkopen",
    "Hold": "Aanhouden",
}
SELL_SIGNAL_NL = {
    "Not held": "Niet in bezit",
    "Hold and monitor": "Aanhouden en volgen",
    "Recommend taking profit": "Winst nemen aanbevolen",
    "Consider partial profit taking": "Overweeg gedeeltelijke winstname",
    "Consider cutting losses": "Overweeg verlies te beperken",
    "Review position; possible stop-loss": "Positie herzien; mogelijke stop-loss",
    "Consider selling to protect capital": "Overweeg te verkopen om kapitaal te beschermen",
}

# The investor funds trades primarily from EUR, with CHF held as a low-inflation
# safe-haven reserve rather than routinely converted for day-to-day purchases.
def compute_funding_advice(currency: str, fx_rates: Dict) -> str:
    if currency == "EUR":
        return "Rechtstreeks in EUR, geen wisselkoers nodig."
    if currency == "USD":
        rate = fx_rates.get("EURUSD")
        rate_txt = f"1 EUR ≈ {rate:.3f} USD" if rate else "koers onbekend"
        return f"Wissel EUR naar USD ({rate_txt}). Houd CHF liever aan als buffer/inflatiehedge."
    if currency == "CHF":
        rate = fx_rates.get("EURCHF")
        rate_txt = f"1 EUR ≈ {rate:.3f} CHF" if rate else "koers onbekend"
        return f"Kan direct vanuit uw CHF-buffer ({rate_txt}), of wissel EUR naar CHF."
    return f"Wissel EUR naar {currency} (actuele koers controleren)."


def build_advice(report: Dict) -> Dict:
    advice = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "all": [],
        "short_term": [],
        "long_term": [],
        "risk_high": [],
        "risk_medium": [],
        "risk_low": [],
    }

    fx_rates = report.get("fx_rates", {})

    for asset in report.get("crypto_analysis", []) + report.get("stock_analysis", []):
        symbol = asset.get("symbol")
        name = asset.get("name")
        score = asset.get("score", 0)
        risk = asset.get("risk_level", "unknown")
        short_note = asset.get("momentum", "")
        long_note = asset.get("long_term_note", "")
        est_profit = asset.get("estimated_profit_pct", 0.0)
        est_cost = asset.get("estimated_cost_pct", 0.0)

        held = asset.get("held", False)
        sell_signal = asset.get("sell_signal", "")
        currency = asset.get("currency", "USD")

        entry = {
            "symbol": symbol,
            "name": name,
            "platform": asset.get("platform", "n/a"),
            "held": held,
            "quantity": asset.get("quantity"),
            "avg_price": asset.get("avg_price"),
            "current_price": asset.get("current_price"),
            "currency": currency,
            "funding_advice": compute_funding_advice(currency, fx_rates),
            "unrealized_pct": asset.get("unrealized_pct"),
            "sell_signal": sell_signal,
            "advice": compute_advice(held, sell_signal, score),
            "short_term": short_note,
            "long_term": long_note,
            "risk": risk,
            "score": score,
            "estimated_profit_pct": est_profit,
            "estimated_cost_pct": est_cost,
        }

        advice["all"].append(entry)

        if risk == "high":
            advice["risk_high"].append(entry)
        elif risk == "medium":
            advice["risk_medium"].append(entry)
        else:
            advice["risk_low"].append(entry)

        if score >= 65:
            advice["short_term"].append(entry)
        if score >= 55 and long_note not in ["high long-term risk", "unclear"]:
            advice["long_term"].append(entry)

    return advice


def summarize_advice(advice: Dict) -> str:
    lines = [
        f"Trading Advisor Summary - {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Short-Term Watchlist (week):",
    ]

    for item in sorted(advice["short_term"], key=lambda x: x["score"], reverse=True)[:10]:
        held_label = "Held" if item.get("held") else "Not held"
        lines.append(
            f"- {item['symbol']} ({item['name']}) [{item.get('platform', 'n/a')}]: {held_label} | advice={item.get('advice')} | qty={item.get('quantity', 'n/a')} | avg={item.get('avg_price', 'n/a')} | unrealized={item.get('unrealized_pct', 'n/a')}% | sell={item.get('sell_signal')} | risk={item['risk']} | short={item['short_term']} | long={item['long_term']} | score={item['score']} | est profit={item['estimated_profit_pct']}% | est cost={item['estimated_cost_pct']}%"
        )

    lines.append("")
    lines.append("Long-Term Candidates (6 months):")
    for item in sorted(advice["long_term"], key=lambda x: x["score"], reverse=True)[:10]:
        held_label = "Held" if item.get("held") else "Not held"
        lines.append(
            f"- {item['symbol']} ({item['name']}) [{item.get('platform', 'n/a')}]: {held_label} | advice={item.get('advice')} | qty={item.get('quantity', 'n/a')} | avg={item.get('avg_price', 'n/a')} | unrealized={item.get('unrealized_pct', 'n/a')}% | sell={item.get('sell_signal')} | risk={item['risk']} | short={item['short_term']} | long={item['long_term']} | score={item['score']} | est profit={item['estimated_profit_pct']}% | est cost={item['estimated_cost_pct']}%"
        )

    lines.append("")
    lines.append("Risk Summary:")
    for risk_level in ["high", "medium", "low"]:
        items = advice[f"risk_{risk_level}"]
        lines.append(f"- {risk_level.title()} risk assets: {len(items)}")

    lines.append("")
    lines.append("Notes:")
    lines.append("- Use this advisor summary as guidance only.")
    lines.append("- Verify liquidity, fees, platform availability, and personal risk tolerance before trading.")
    lines.append("- This agent does not execute trades.")

    return "\n".join(lines)


def save_output(advice: Dict, summary_text: str) -> None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(advice, fh, indent=2)

    with open(SUMMARY_PATH, "w", encoding="utf-8") as fh:
        fh.write(summary_text)

    logger.info(f"Advisor output saved to {OUTPUT_PATH}")
    logger.info(f"Advisor summary saved to {SUMMARY_PATH}")


def airtable_find_record_id(symbol: str) -> Optional[str]:
    import requests

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    escaped_symbol = symbol.replace("'", "\\'")
    params = {"filterByFormula": f"{{Asset}} = '{escaped_symbol}'", "maxRecords": 1}
    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    matches = response.json().get("records", [])
    return matches[0]["id"] if matches else None


def airtable_upsert_record(symbol: str, record: Dict) -> Optional[Dict]:
    if not AIRTABLE_ENABLED:
        return None

    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        logger.warning("Airtable is enabled but API key or Base ID is missing.")
        return None

    try:
        import requests
    except ImportError:
        logger.error("Install requests to use Airtable: python -m pip install requests")
        return None

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"fields": record}
    existing_id = airtable_find_record_id(symbol)
    if existing_id:
        response = requests.patch(f"{url}/{existing_id}", headers=headers, json=payload, timeout=15)
    else:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def airtable_sync(advice: Dict) -> None:
    if not AIRTABLE_ENABLED:
        logger.info("Airtable sync skipped because TRADING_ADVISOR_USE_AIRTABLE is not enabled.")
        return

    logger.info("Syncing advisor data to Airtable...")
    for item in advice["all"]:
        symbol = item["symbol"]
        current_price = item.get("current_price")
        quantity = item.get("quantity")
        current_value = (
            current_price * quantity if current_price is not None and quantity is not None else None
        )
        sell_signal = item.get("sell_signal", "")
        record = {
            "Asset": item["symbol"],
            "Name": item["name"],
            "Platform": item.get("platform", "n/a"),
            "Held": "Ja" if item.get("held") else "Nee",
            "Quantity": item.get("quantity"),
            "Avg Price": item.get("avg_price"),
            "Current Price": current_price,
            "Current Value": current_value,
            "Currency": item.get("currency"),
            "Funding Advice": item.get("funding_advice"),
            "Unrealized %": item.get("unrealized_pct"),
            "Sell Signal": SELL_SIGNAL_NL.get(sell_signal, sell_signal),
            "Advice": ADVICE_NL.get(item.get("advice"), item.get("advice")),
            "Short Term (week)": MOMENTUM_NL.get(item["short_term"], item["short_term"]),
            "Long Term (6 months)": LONG_TERM_NOTE_NL.get(item["long_term"], item["long_term"]),
            "Risk": RISK_NL.get(item["risk"], item["risk"]),
            "Score": item["score"],
            "Estimated Profit %": item["estimated_profit_pct"],
            "Estimated Cost %": item["estimated_cost_pct"],
            "Source": "Onderzoeksrapport",
        }
        try:
            airtable_upsert_record(symbol, record)
        except Exception as exc:
            logger.error(f"Airtable record failed: {exc}")


def main() -> None:
    try:
        report = load_report()
    except Exception as exc:
        logger.error(f"Failed to load research report: {exc}")
        return

    advice = build_advice(report)
    summary = summarize_advice(advice)
    save_output(advice, summary)

    if AIRTABLE_ENABLED:
        airtable_sync(advice)

    print(summary)


if __name__ == "__main__":
    main()

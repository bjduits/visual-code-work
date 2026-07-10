#!/usr/bin/env python3
"""
AI Trading Advisor using OpenAI.

This script provides an example of how to generate advisor text from OpenAI,
using the existing research report as input.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

from dotenv import load_dotenv

try:
    import openai
except ImportError:
    openai = None

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
        logging.FileHandler(tmp_dir / "trading_advisor_openai.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

REPORT_PATH = tmp_dir / "trading_research_report.json"
OUTPUT_PATH = tmp_dir / "trading_advisor_openai_output.txt"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

PROMPT_TEMPLATE = (
    "You are a trading advisor. Analyze the following asset data for short-term (week) and long-term (6 months) outlooks. "
    "Provide risk guidance, estimated profit percentages, and a clear summary. Do not provide live trade execution.\n\n"
)


def load_report() -> Dict:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Research report not found: {REPORT_PATH}")
    with open(REPORT_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_prompt(report: Dict) -> str:
    summary_lines = [PROMPT_TEMPLATE, "Asset analysis:"]
    for asset in report.get("crypto_analysis", []) + report.get("stock_analysis", []):
        summary_lines.append(
            f"- {asset.get('symbol')} ({asset.get('name')}): score={asset.get('score')} risk={asset.get('risk_level')} "
            f"short={asset.get('momentum')} long={asset.get('long_term_note')} profit={asset.get('estimated_profit_pct')}% cost={asset.get('estimated_cost_pct')}%"
        )
    summary_lines.append("\nProvide a concise advisor summary.")
    return "\n".join(summary_lines)


def run_openai(prompt: str) -> str:
    if openai is None:
        raise ImportError("Install openai with: python -m pip install openai")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required in .env to use OpenAI.")

    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a trading research advisor."},
                  {"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def save_output(content: str) -> None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(content)
    logger.info(f"OpenAI advisor output saved to {OUTPUT_PATH}")


def main() -> None:
    try:
        report = load_report()
    except Exception as exc:
        logger.error(f"Failed to load research report: {exc}")
        return

    prompt = build_prompt(report)
    try:
        answer = run_openai(prompt)
    except Exception as exc:
        logger.error(f"OpenAI request failed: {exc}")
        return

    save_output(answer)
    print(answer)


if __name__ == "__main__":
    main()

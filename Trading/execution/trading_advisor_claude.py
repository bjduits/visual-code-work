#!/usr/bin/env python3
"""
AI Trading Advisor using Claude (Anthropic API).

Uses the existing trading_research_report.json as input and generates an
advisor summary via the Anthropic Messages API.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

try:
    import anthropic
except ImportError:
    anthropic = None

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

root_dir = Path(__file__).parent.parent
tmp_dir = root_dir / ".tmp"
tmp_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(tmp_dir / "trading_advisor_claude.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

REPORT_PATH = tmp_dir / "trading_research_report.json"
OUTPUT_PATH = tmp_dir / "trading_advisor_claude_output.txt"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# Defaults to Opus (most capable). For a cheaper/faster model, set CLAUDE_MODEL
# in .env to e.g. "claude-sonnet-5" or "claude-haiku-4-5".
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")

PROMPT_TEMPLATE = (
    "You are a trading research advisor. Analyze the following asset data for "
    "short-term (week) and long-term (6 months) outlooks. Provide risk guidance, "
    "estimated profit percentages, and a clear, concise summary. Do not provide "
    "live trade execution instructions.\n\n"
)


def load_report() -> Dict:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Research report not found: {REPORT_PATH}")
    with open(REPORT_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_prompt(report: Dict) -> str:
    lines = [PROMPT_TEMPLATE, "Asset analysis:"]
    for asset in report.get("crypto_analysis", []) + report.get("stock_analysis", []):
        lines.append(
            f"- {asset.get('symbol')} ({asset.get('name')}): score={asset.get('score')} "
            f"risk={asset.get('risk_level')} short={asset.get('momentum')} "
            f"long={asset.get('long_term_note')} profit={asset.get('estimated_profit_pct')}% "
            f"cost={asset.get('estimated_cost_pct')}% platform={asset.get('platform', 'n/a')}"
        )
    lines.append("\nProvide a concise advisor summary.")
    return "\n".join(lines)


def run_claude(prompt: str) -> str:
    if anthropic is None:
        raise ImportError("Install the Anthropic SDK with: python -m pip install anthropic")
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is required in .env to use Claude.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system="You are a trading research advisor. This is not financial advice.",
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()


def save_output(content: str) -> None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(content)
    logger.info(f"Claude advisor output saved to {OUTPUT_PATH}")


def main() -> None:
    try:
        report = load_report()
    except Exception as exc:
        logger.error(f"Failed to load research report: {exc}")
        return

    prompt = build_prompt(report)
    try:
        answer = run_claude(prompt)
    except Exception as exc:
        logger.error(f"Claude request failed: {exc}")
        return

    save_output(answer)
    print(answer)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Free, offline AI trading advisor using a local model via the gpt4all package.

Reads USE_LOCAL_LLM and GPT4ALL_MODEL_PATH from .env and uses the existing
trading_research_report.json as input. No API key or network call to a
third-party LLM provider is required -- inference runs entirely on this
machine. The model file is downloaded automatically on first run (from
gpt4all's own official model list) and cached under ~/.cache/gpt4all.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

root_dir = Path(__file__).parent.parent
tmp_dir = root_dir / ".tmp"
tmp_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(tmp_dir / "trading_advisor_local.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

REPORT_PATH = tmp_dir / "trading_research_report.json"
OUTPUT_PATH = tmp_dir / "trading_advisor_local_output.txt"

USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "0") == "1"
MODEL_NAME = os.getenv("GPT4ALL_MODEL_PATH", "")

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


def run_local_llm(prompt: str) -> str:
    try:
        from gpt4all import GPT4All
    except ImportError:
        raise ImportError(
            "Install the local LLM package with: python -m pip install gpt4all"
        )

    if not MODEL_NAME:
        raise ValueError(
            "GPT4ALL_MODEL_PATH is not set in .env. Set it to an official gpt4all "
            "model filename, e.g. Llama-3.2-3B-Instruct-Q4_0.gguf"
        )

    logger.info(
        f"Loading local model '{MODEL_NAME}' (downloads automatically on first "
        "run and is cached under ~/.cache/gpt4all -- this can take a while)..."
    )
    model = GPT4All(MODEL_NAME, allow_download=True, n_ctx=4096)

    with model.chat_session(system_prompt="You are a trading research advisor."):
        response = model.generate(prompt, max_tokens=600, temp=0.7)
    return response.strip()


def save_output(content: str) -> None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(content)
    logger.info(f"Local advisor output saved to {OUTPUT_PATH}")


def main() -> None:
    if not USE_LOCAL_LLM:
        logger.error("USE_LOCAL_LLM is not enabled. Set USE_LOCAL_LLM=1 in .env to use this script.")
        sys.exit(1)

    try:
        report = load_report()
    except Exception as exc:
        logger.error(f"Failed to load research report: {exc}")
        return

    prompt = build_prompt(report)
    try:
        answer = run_local_llm(prompt)
    except Exception as exc:
        logger.error(f"Local LLM request failed: {exc}")
        return

    save_output(answer)
    print(answer)


if __name__ == "__main__":
    main()

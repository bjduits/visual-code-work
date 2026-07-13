#!/usr/bin/env python3
"""
Gather Eurozone and US CPI/inflation data.

This script:
1. Fetches Eurozone HICP (all-items annual rate of change) from Eurostat
2. Fetches US CPI (all-items) from the BLS public API and derives YoY/MoM change
3. Fetches EUR/USD and EUR/CHF FX rates for context
4. Writes a report to .tmp/

This is a research tool only. It is not financial advice.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

root_dir = Path(__file__).parent.parent
tmp_dir = root_dir / ".tmp"
tmp_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(tmp_dir / "cpi_research.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

EUROSTAT_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr"
BLS_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
BLS_SERIES_YOY = "CUUR0000SA0"   # CPI-U, all items, not seasonally adjusted (for YoY)
BLS_SERIES_MOM = "CUSR0000SA0"   # CPI-U, all items, seasonally adjusted (for MoM)


def fetch_fx_rate(pair_symbol: str) -> Optional[float]:
    import requests

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair_symbol}"
    params = {"range": "1d", "interval": "1d"}
    try:
        response = requests.get(url, params=params, headers=YAHOO_HEADERS, timeout=15)
        response.raise_for_status()
        meta = response.json().get("chart", {}).get("result", [{}])[0].get("meta", {})
        return meta.get("regularMarketPrice")
    except Exception as exc:
        logger.warning(f"Could not fetch FX rate for {pair_symbol}: {exc}")
        return None


def _jsonstat_time_series(data: Dict) -> Dict[str, float]:
    """Flatten a JSON-stat 2.0 payload into {period: value}, assuming every
    non-time dimension has size 1 (true when the Eurostat query fixes geo/
    unit/coicop to a single value each)."""
    ids: List[str] = data["id"]
    sizes: List[int] = data["size"]
    strides = [1] * len(ids)
    for i in range(len(ids) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]

    time_pos = ids.index("time")
    time_stride = strides[time_pos]
    time_index = data["dimension"]["time"]["category"]["index"]
    values = data["value"]

    result = {}
    for period, idx in time_index.items():
        flat_index = idx * time_stride
        val = values.get(str(flat_index))
        if val is not None:
            result[period] = float(val)
    return dict(sorted(result.items()))


def fetch_eurozone_hicp() -> Optional[Dict]:
    import requests

    params = {
        "format": "JSON",
        "lang": "en",
        "geo": "EA",
        "unit": "RCH_A",
        "coicop": "CP00",
    }
    response = requests.get(EUROSTAT_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    series = _jsonstat_time_series(data)
    if not series:
        logger.warning("Eurostat returned no HICP data points")
        return None

    periods = list(series.keys())
    latest_period = periods[-1]
    latest_value = series[latest_period]
    previous_period = periods[-2] if len(periods) > 1 else None
    previous_value = series.get(previous_period) if previous_period else None

    trend = "flat"
    if previous_value is not None:
        if latest_value > previous_value:
            trend = "up"
        elif latest_value < previous_value:
            trend = "down"

    history = dict(list(series.items())[-13:])

    logger.info(f"Fetched Eurozone HICP: {latest_period} = {latest_value}%")
    return {
        "label": "Eurozone HICP, all-items annual rate of change",
        "unit": "% year-on-year",
        "latest_period": latest_period,
        "latest_value": latest_value,
        "previous_period": previous_period,
        "previous_value": previous_value,
        "trend": trend,
        "history": history,
        "source": "Eurostat (prc_hicp_manr, geo=EA, coicop=CP00)",
    }


def _bls_series_to_dict(series_data: List[Dict]) -> Dict[Tuple[int, int], float]:
    out = {}
    for point in series_data:
        period = point.get("period", "")
        if not period.startswith("M") or period == "M13":
            continue
        try:
            year = int(point["year"])
            month = int(period[1:])
            value = float(point["value"])
        except (KeyError, ValueError):
            continue
        out[(year, month)] = value
    return out


def fetch_us_cpi() -> Optional[Dict]:
    import requests

    current_year = datetime.now().year
    payload = {
        "seriesid": [BLS_SERIES_YOY, BLS_SERIES_MOM],
        "startyear": str(current_year - 3),
        "endyear": str(current_year),
    }
    response = requests.post(BLS_URL, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "REQUEST_SUCCEEDED":
        logger.warning(f"BLS API request did not succeed: {data.get('message')}")
        return None

    series_by_id = {s["seriesID"]: s["data"] for s in data.get("Results", {}).get("series", [])}
    nsa = _bls_series_to_dict(series_by_id.get(BLS_SERIES_YOY, []))
    sa = _bls_series_to_dict(series_by_id.get(BLS_SERIES_MOM, []))

    if not nsa or not sa:
        logger.warning("BLS API returned no usable CPI data points")
        return None

    def period_label(year: int, month: int) -> str:
        return f"{year:04d}-{month:02d}"

    # YoY history from the not-seasonally-adjusted series
    yoy_history = {}
    for (year, month), value in sorted(nsa.items()):
        prior = nsa.get((year - 1, month))
        if prior:
            yoy_history[period_label(year, month)] = round((value - prior) / prior * 100.0, 2)
    yoy_history = dict(list(yoy_history.items())[-13:])

    # MoM history from the seasonally-adjusted series
    sa_sorted = sorted(sa.items())
    mom_history = {}
    for i in range(1, len(sa_sorted)):
        (year, month), value = sa_sorted[i]
        (_, _), prev_value = sa_sorted[i - 1]
        if prev_value:
            mom_history[period_label(year, month)] = round((value - prev_value) / prev_value * 100.0, 2)
    mom_history = dict(list(mom_history.items())[-13:])

    if not yoy_history or not mom_history:
        logger.warning("Not enough BLS history to compute YoY/MoM CPI change")
        return None

    yoy_periods = list(yoy_history.keys())
    mom_periods = list(mom_history.keys())

    latest_yoy_period = yoy_periods[-1]
    latest_yoy = yoy_history[latest_yoy_period]
    previous_yoy = yoy_history.get(yoy_periods[-2]) if len(yoy_periods) > 1 else None

    latest_mom_period = mom_periods[-1]
    latest_mom = mom_history[latest_mom_period]

    trend = "flat"
    if previous_yoy is not None:
        if latest_yoy > previous_yoy:
            trend = "up"
        elif latest_yoy < previous_yoy:
            trend = "down"

    logger.info(f"Fetched US CPI: {latest_yoy_period} YoY = {latest_yoy}%, MoM = {latest_mom}%")
    return {
        "label": "US CPI-U, all-items",
        "unit": "% change",
        "latest_period": latest_yoy_period,
        "latest_value": latest_yoy,
        "previous_period": yoy_periods[-2] if len(yoy_periods) > 1 else None,
        "previous_value": previous_yoy,
        "trend": trend,
        "latest_mom_period": latest_mom_period,
        "latest_mom_value": latest_mom,
        "history": yoy_history,
        "mom_history": mom_history,
        "source": f"BLS API ({BLS_SERIES_YOY} YoY, {BLS_SERIES_MOM} MoM)",
    }


def build_summary(eurozone: Optional[Dict], us: Optional[Dict], fx_rates: Dict) -> str:
    lines = [
        f"CPI Research Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]

    if eurozone:
        lines.append("Eurozone HICP (annual % change):")
        lines.append(
            f"- {eurozone['latest_period']}: {eurozone['latest_value']}% "
            f"(previous {eurozone['previous_period']}: {eurozone['previous_value']}%, trend: {eurozone['trend']})"
        )
    else:
        lines.append("Eurozone HICP: data unavailable this run.")

    lines.append("")

    if us:
        lines.append("US CPI-U (all items):")
        lines.append(
            f"- YoY {us['latest_period']}: {us['latest_value']}% "
            f"(previous {us['previous_period']}: {us['previous_value']}%, trend: {us['trend']})"
        )
        lines.append(f"- MoM {us['latest_mom_period']}: {us['latest_mom_value']}%")
    else:
        lines.append("US CPI: data unavailable this run.")

    lines.append("")
    lines.append("FX rates:")
    lines.append(f"- EUR/USD: {fx_rates.get('EURUSD')}")
    lines.append(f"- EUR/CHF: {fx_rates.get('EURCHF')}")

    lines.append("")
    lines.append("Notes:")
    lines.append("- This is a research summary of published inflation statistics, not financial advice.")
    lines.append("- Eurostat HICP flash estimates can be revised; treat the latest month as provisional.")

    return "\n".join(lines)


def save_report(report: Dict, summary_text: str) -> None:
    report_path = tmp_dir / "cpi_research_report.json"
    summary_path = tmp_dir / "cpi_research_summary.txt"

    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write(summary_text)

    logger.info(f"Report saved to {report_path}")
    logger.info(f"Summary saved to {summary_path}")


def main():
    try:
        import requests  # noqa: F401
    except ImportError:
        logger.error("The 'requests' package is required. Install it with: python -m pip install requests")
        sys.exit(1)

    eurozone = None
    us = None

    try:
        eurozone = fetch_eurozone_hicp()
    except Exception as exc:
        logger.error(f"Eurostat HICP fetch failed: {exc}")

    try:
        us = fetch_us_cpi()
    except Exception as exc:
        logger.error(f"BLS US CPI fetch failed: {exc}")

    if eurozone is None and us is None:
        logger.error("Both Eurozone and US CPI fetches failed; nothing to report")
        sys.exit(1)

    fx_rates = {
        "EURUSD": fetch_fx_rate("EURUSD=X"),
        "EURCHF": fetch_fx_rate("EURCHF=X"),
    }

    summary = build_summary(eurozone, us, fx_rates)
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "eurozone_hicp": eurozone,
        "us_cpi": us,
        "fx_rates": fx_rates,
    }
    save_report(report, summary)

    print(summary)


if __name__ == "__main__":
    main()

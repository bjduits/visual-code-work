#!/usr/bin/env python3
"""
Gather SAP insights from multiple sources and render them as a PDF report.

This script:
1. Fetches insights from multiple sources (news APIs, curated SAP sources)
2. Deduplicates and filters for relevance
3. Renders a PDF report to .tmp/

Environment variables:
- NEWSAPI_KEY: (Optional) NewsAPI key for better coverage
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
from xml.sax.saxutils import escape

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Create logs/output directories
root_dir = Path(__file__).parent.parent
tmp_dir = root_dir / ".tmp"
tmp_dir.mkdir(exist_ok=True)

REPORT_DATE = datetime.now().strftime("%Y-%m-%d")
PDF_OUTPUT_PATH = tmp_dir / f"sap_insights_report_{REPORT_DATE}.pdf"
REPORT_AUTHOR = "Bram-Jan Duits"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(tmp_dir / "sap_insights_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SAPInsightGatherer:
    """Gathers SAP insights from multiple sources."""

    def __init__(self):
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.insights: List[Dict] = []
        self.seen_urls: Set[str] = set()

    def gather_insights(self) -> List[Dict]:
        """Gather insights from multiple sources."""
        logger.info("Starting insight gathering...")

        sources_tried = 0
        sources_succeeded = 0

        try:
            self._fetch_from_newsapi()
            sources_succeeded += 1
        except Exception as e:
            logger.warning(f"NewsAPI failed: {e}")
        sources_tried += 1

        try:
            self._fetch_from_builtin_sources()
            sources_succeeded += 1
        except Exception as e:
            logger.warning(f"Built-in sources failed: {e}")
        sources_tried += 1

        logger.info(f"Gathered {len(self.insights)} insights from {sources_succeeded}/{sources_tried} sources")

        if not self.insights:
            logger.warning("No insights found from any source")
            return []

        return self._deduplicate_and_sort()

    def _fetch_from_newsapi(self):
        """Fetch from NewsAPI if available."""
        if not self.newsapi_key:
            logger.info("Skipping NewsAPI (no key configured)")
            return

        try:
            import requests

            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "SAP",
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": self.newsapi_key,
                "pageSize": 15
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("articles"):
                for article in data["articles"]:
                    if article["url"] not in self.seen_urls:
                        self.insights.append({
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "url": article.get("url", ""),
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "published": article.get("publishedAt", ""),
                        })
                        self.seen_urls.add(article["url"])
                logger.info(f"Fetched {len(data['articles'])} articles from NewsAPI")

        except ImportError:
            logger.warning("requests library not installed, skipping NewsAPI")
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")

    def _fetch_from_builtin_sources(self):
        """Add curated SAP insight entries as a fallback/complement."""
        self.insights.extend([
            {
                "title": "Latest SAP Cloud Solutions",
                "description": "Stay updated on SAP's cloud innovations and enterprise software solutions.",
                "url": "https://www.sap.com/products/cloud.html",
                "source": "SAP Official",
                "published": datetime.now().isoformat(),
            },
            {
                "title": "SAP Analytics Cloud Updates",
                "description": "Explore the latest updates in SAP Analytics Cloud and business intelligence.",
                "url": "https://www.sap.com/products/analytics/sac.html",
                "source": "SAP Official",
                "published": datetime.now().isoformat(),
            },
            {
                "title": "S/4HANA News & Updates",
                "description": "Get the latest on SAP's flagship ERP system S/4HANA.",
                "url": "https://www.sap.com/products/erp/s4hana.html",
                "source": "SAP Official",
                "published": datetime.now().isoformat(),
            }
        ])

        logger.info("Added curated built-in sources")

    def _deduplicate_and_sort(self) -> List[Dict]:
        """Remove duplicates and sort by recency."""
        unique = {}
        for insight in self.insights:
            url = insight.get("url", "")
            if url and url not in unique:
                unique[url] = insight

        sorted_insights = sorted(
            unique.values(),
            key=lambda x: x.get("published", ""),
            reverse=True
        )

        return sorted_insights[:10]


def build_pdf(insights: List[Dict], generated_at: str) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleFriendly", parent=styles["Title"], textColor=colors.HexColor("#0070C0")
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"], textColor=colors.grey,
        alignment=TA_CENTER, fontSize=10, spaceAfter=16,
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], textColor=colors.HexColor("#0070C0"),
        spaceBefore=14, spaceAfter=8,
    )
    body = ParagraphStyle("BodyFriendly", parent=styles["BodyText"], leading=15, spaceAfter=6)
    meta = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=8, textColor=colors.grey, spaceAfter=10)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    doc = SimpleDocTemplate(
        str(PDF_OUTPUT_PATH), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        title="SAP Insights Report", author=REPORT_AUTHOR, subject="SAP Insights Report",
    )
    story = []

    story.append(Paragraph("SAP Insights Report", title_style))
    story.append(Paragraph(
        f"Opgesteld door {escape(REPORT_AUTHOR)} &middot; Gegenereerd op {escape(generated_at)}",
        subtitle_style,
    ))

    if not insights:
        story.append(Paragraph(
            "Er zijn deze keer geen nieuwe SAP-inzichten gevonden. Probeer het later opnieuw.",
            body,
        ))
    else:
        story.append(Paragraph("Laatste SAP-nieuws en ontwikkelingen", h2))
        for i, insight in enumerate(insights, 1):
            title = escape(insight.get("title", "Untitled"))
            description = escape(insight.get("description", "") or "")
            url = escape(insight.get("url", "#"))
            source = escape(insight.get("source", "Unknown"))
            published = insight.get("published", "")

            if published:
                try:
                    pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    published = pub_date.strftime("%d %B %Y")
                except Exception:
                    pass

            story.append(Paragraph(f"<b>{i}. {title}</b>", body))
            if description:
                story.append(Paragraph(description, body))
            story.append(Paragraph(
                f"{source}" + (f" &middot; {escape(published)}" if published else "") +
                f" &middot; <link href='{url}'>{url}</link>",
                meta,
            ))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Dit rapport is automatisch samengesteld op basis van publieke nieuwsbronnen en "
        "SAP-officiele kanalen, uitsluitend ter informatie.",
        small,
    ))

    doc.build(story)
    logger.info(f"PDF-rapport opgeslagen op {PDF_OUTPUT_PATH}")


def main():
    gatherer = SAPInsightGatherer()
    insights = gatherer.gather_insights()

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        build_pdf(insights, generated_at)
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}", exc_info=True)
        sys.exit(1)

    print(f"PDF report saved to: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    main()

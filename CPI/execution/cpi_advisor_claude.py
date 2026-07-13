#!/usr/bin/env python3
"""
AI CPI/Inflation Advisor using Claude (Anthropic API).

Uses the existing cpi_research_report.json as input, asks Claude for a
friendly Dutch-language narrative outlook on Eurozone and US inflation
(grounded only in the fetched CPI figures and FX rates), and renders a PDF
report. The PDF is then emailed as an attachment via Gmail SMTP.
"""

import os
import sys
import json
import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, Optional
from xml.sax.saxutils import escape

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

try:
    import anthropic
except ImportError:
    anthropic = None

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

root_dir = Path(__file__).parent.parent
tmp_dir = root_dir / ".tmp"
tmp_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(tmp_dir / "cpi_advisor_claude.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

REPORT_PATH = tmp_dir / "cpi_research_report.json"
TEXT_OUTPUT_PATH = tmp_dir / "cpi_advisor_claude_output.txt"
REPORT_DATE = datetime.now().strftime("%Y-%m-%d")
PDF_OUTPUT_PATH = tmp_dir / f"cpi_advisor_claude_report_{REPORT_DATE}.pdf"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
REPORT_AUTHOR = "Bram-Jan Duits"

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
CPI_EMAIL_TO = os.getenv("CPI_EMAIL_TO", GMAIL_ADDRESS)

TREND_NL = {"up": "stijgend", "down": "dalend", "flat": "stabiel"}


def load_report() -> Dict:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(
            f"CPI research report not found: {REPORT_PATH}. "
            "Run gather_cpi_research.py first."
        )
    with open(REPORT_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_prompt(eurozone: Optional[Dict], us: Optional[Dict], fx_rates: Dict) -> str:
    eur_usd = fx_rates.get("EURUSD")
    eur_chf = fx_rates.get("EURCHF")

    lines = [
        "Je bent een warme, vriendelijke financieel adviseur die schrijft voor een "
        "particuliere belegger. De belegger houdt zijn geld voornamelijk in EUR aan, "
        "met een deel in Zwitserse frank (CHF) als reserve, en heeft ook USD-genoteerde "
        "beleggingen. Schrijf in het Nederlands, in een bemoedigende, prettig leesbare "
        "stijl (platte tekst, geen kopjes, geen markdown, geen opsommingstekens), "
        "verdeeld in 5-6 korte alinea's die in deze volgorde het volgende behandelen:\n"
        "1) Een korte, neutrale opening over de laatste inflatiecijfers voor de "
        "eurozone en de Verenigde Staten, puur gebaseerd op de cijfers hieronder.\n"
        "2) Wat de trend (stijgend/dalend/stabiel) betekent voor de koopkracht van "
        "EUR-tegoeden, en waarom de Zwitserse frank historisch als inflatie-arme "
        "vluchthavenvaluta geldt (blijf hier algemeen, verzin geen actuele CHF-inflatiecijfers).\n"
        "3) Wat de Amerikaanse inflatie betekent voor USD-genoteerde posities en de "
        "wisselkoers EUR/USD, gebruik makend van de huidige koers hieronder.\n"
        "4) Wat dit in algemene termen kan betekenen voor spaargeld versus beleggen "
        "(reeel rendement), zonder concrete koop- of verkoopadviezen te geven.\n"
        "5) Een voorzichtige alinea over wat de komende maanden om in de gaten te "
        "houden is (bijvoorbeeld of de trend doorzet), zonder voorspellingen als feiten "
        "te presenteren.\n"
        "6) Een vriendelijke afsluiting die benadrukt dat dit educatief onderzoek is, "
        "geen financieel advies, en dat de lezer altijd de meest actuele officiele "
        "cijfers (Eurostat, BLS) zelf moet controleren.\n\n"
        "Inflatiedata:\n"
    ]

    if eurozone:
        lines.append(
            f"- Eurozone HICP (jaar-op-jaar): {eurozone['latest_period']} = "
            f"{eurozone['latest_value']}% (vorige periode {eurozone['previous_period']} = "
            f"{eurozone['previous_value']}%, trend: {eurozone['trend']})"
        )
    else:
        lines.append("- Eurozone HICP: geen data beschikbaar deze run.")

    if us:
        lines.append(
            f"- VS CPI jaar-op-jaar: {us['latest_period']} = {us['latest_value']}% "
            f"(vorige periode {us['previous_period']} = {us['previous_value']}%, trend: {us['trend']})"
        )
        lines.append(
            f"- VS CPI maand-op-maand (seizoensgecorrigeerd): {us['latest_mom_period']} = "
            f"{us['latest_mom_value']}%"
        )
    else:
        lines.append("- VS CPI: geen data beschikbaar deze run.")

    lines.append(
        f"- Wisselkoersen: 1 EUR ≈ {eur_usd} USD, 1 EUR ≈ {eur_chf} CHF"
        if eur_usd and eur_chf else "- Wisselkoersen konden niet worden opgehaald."
    )

    return "\n".join(lines)


def run_claude(prompt: str) -> str:
    if anthropic is None:
        raise ImportError("Install the Anthropic SDK with: python -m pip install anthropic")
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is required in .env to use Claude.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=(
            "Je bent een vriendelijke, toegankelijke financieel adviseur die in het "
            "Nederlands schrijft. Dit is educatief onderzoek, geen financieel advies."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()


def save_text_output(content: str) -> None:
    with open(TEXT_OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(content)
    logger.info(f"Claude advisor narrative saved to {TEXT_OUTPUT_PATH}")


def build_pdf(eurozone: Optional[Dict], us: Optional[Dict], narrative: str, fx_rates: Dict, generated_at: str) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleFriendly", parent=styles["Title"], textColor=colors.HexColor("#1a3d5c")
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"], textColor=colors.grey,
        alignment=TA_CENTER, fontSize=10, spaceAfter=16,
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], textColor=colors.HexColor("#1a3d5c"),
        spaceBefore=14, spaceAfter=8,
    )
    body = ParagraphStyle("BodyFriendly", parent=styles["BodyText"], leading=15, spaceAfter=8)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    doc = SimpleDocTemplate(
        str(PDF_OUTPUT_PATH), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        title="CPI / Inflatie Rapport", author=REPORT_AUTHOR, subject="CPI Advisor Report",
    )
    story = []

    story.append(Paragraph("Uw Maandelijkse Inflatie (CPI) Rapport", title_style))
    story.append(Paragraph(
        f"Opgesteld door {escape(REPORT_AUTHOR)} &middot; Gegenereerd op "
        f"{escape(generated_at)} &middot; Educatief onderzoek, geen financieel advies",
        subtitle_style,
    ))

    story.append(Paragraph("In één oogopslag", h2))
    table_data = [["Regio", "Indicator", "Periode", "Waarde", "Vorige", "Trend"]]
    if eurozone:
        table_data.append([
            "Eurozone", "HICP jaar-op-jaar", eurozone["latest_period"],
            f"{eurozone['latest_value']:.1f}%",
            f"{eurozone['previous_value']:.1f}%" if eurozone["previous_value"] is not None else "n.v.t.",
            TREND_NL.get(eurozone["trend"], eurozone["trend"]),
        ])
    if us:
        table_data.append([
            "VS", "CPI jaar-op-jaar", us["latest_period"],
            f"{us['latest_value']:.2f}%",
            f"{us['previous_value']:.2f}%" if us["previous_value"] is not None else "n.v.t.",
            TREND_NL.get(us["trend"], us["trend"]),
        ])
        table_data.append([
            "VS", "CPI maand-op-maand (SA)", us["latest_mom_period"],
            f"{us['latest_mom_value']:.2f}%", "-", "-",
        ])

    tbl = Table(
        table_data,
        colWidths=[2.4 * cm, 4.4 * cm, 2.4 * cm, 2.2 * cm, 2.2 * cm, 2.4 * cm],
        repeatRows=1,
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3d5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

    if eurozone and eurozone.get("history"):
        story.append(Paragraph("Eurozone HICP — laatste maanden (jaar-op-jaar %)", h2))
        hist_row = [["Periode"] + list(eurozone["history"].keys())]
        hist_row.append(["Waarde"] + [f"{v:.1f}%" for v in eurozone["history"].values()])
        hist_tbl = Table(hist_row, repeatRows=1)
        hist_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2f6")),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ]))
        story.append(hist_tbl)
        story.append(Spacer(1, 12))

    if us and us.get("history"):
        story.append(Paragraph("VS CPI — laatste maanden (jaar-op-jaar %)", h2))
        hist_row = [["Periode"] + list(us["history"].keys())]
        hist_row.append(["Waarde"] + [f"{v:.1f}%" for v in us["history"].values()])
        hist_tbl = Table(hist_row, repeatRows=1)
        hist_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2f6")),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ]))
        story.append(hist_tbl)
        story.append(Spacer(1, 12))

    story.append(Paragraph("Vooruitzicht", h2))
    for para in narrative.split("\n\n"):
        para = para.strip()
        if para:
            story.append(Paragraph(escape(para), body))

    eur_usd = fx_rates.get("EURUSD")
    eur_chf = fx_rates.get("EURCHF")
    story.append(Paragraph("Wisselkoersen", h2))
    story.append(Paragraph(
        f"Actuele koersen: 1 EUR ≈ {eur_usd:.3f} USD, 1 EUR ≈ {eur_chf:.3f} CHF."
        if eur_usd and eur_chf else "Actuele wisselkoersen konden niet worden opgehaald.",
        body,
    ))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Dit rapport is gegenereerd op basis van officiele inflatiecijfers (Eurostat HICP, "
        "BLS CPI-U) en een AI-samenvatting, uitsluitend voor educatieve doeleinden. Dit is "
        "geen financieel advies. Eurostat flash-schattingen kunnen nog worden herzien. "
        "Controleer altijd de meest actuele officiele cijfers voordat u beslissingen neemt.",
        small,
    ))

    doc.build(story)
    logger.info(f"CPI PDF-rapport opgeslagen op {PDF_OUTPUT_PATH}")


def send_email_with_pdf(pdf_path: Path, generated_at: str) -> None:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.warning(
            "GMAIL_ADDRESS/GMAIL_APP_PASSWORD not configured in .env; "
            "skipping email send. PDF remains available locally."
        )
        return
    if not CPI_EMAIL_TO:
        logger.warning("CPI_EMAIL_TO not configured in .env; skipping email send.")
        return

    msg = EmailMessage()
    msg["Subject"] = f"CPI / Inflatie Rapport - {generated_at}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = CPI_EMAIL_TO
    msg.set_content(
        "Bijgevoegd het maandelijkse CPI/inflatie rapport (Eurozone HICP en VS CPI).\n\n"
        "Dit is automatisch gegenereerd onderzoek, geen financieel advies.\n"
    )

    with open(pdf_path, "rb") as fh:
        msg.add_attachment(
            fh.read(),
            maintype="application",
            subtype="pdf",
            filename=pdf_path.name,
        )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        logger.info(f"CPI PDF emailed to {CPI_EMAIL_TO}")
    except Exception as exc:
        logger.error(f"Failed to send CPI report email: {exc}")


def main() -> None:
    try:
        report = load_report()
    except Exception as exc:
        logger.error(f"Failed to load CPI research report: {exc}")
        return

    eurozone = report.get("eurozone_hicp")
    us = report.get("us_cpi")
    fx_rates = report.get("fx_rates", {})

    prompt = build_prompt(eurozone, us, fx_rates)
    try:
        narrative = run_claude(prompt)
    except Exception as exc:
        logger.error(f"Claude request failed: {exc}")
        return

    save_text_output(narrative)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        build_pdf(eurozone, us, narrative, fx_rates, generated_at)
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}")
        return

    send_email_with_pdf(PDF_OUTPUT_PATH, generated_at)

    print(narrative)
    print(f"\nPDF report saved to: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    main()

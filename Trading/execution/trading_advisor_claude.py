#!/usr/bin/env python3
"""
AI Trading Advisor using Claude (Anthropic API).

Uses the existing trading_research_report.json as input, asks Claude for a
friendly Dutch-language narrative outlook (including macro risks and
opportunities grounded in recent news), and renders a combined PDF report
with buy/sell recommendations, short- and long-term outlooks, and recent
history for stocks, currencies, commodities, and cryptocurrencies.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
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
        logging.FileHandler(tmp_dir / "trading_advisor_claude.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

REPORT_PATH = tmp_dir / "trading_research_report.json"
TEXT_OUTPUT_PATH = tmp_dir / "trading_advisor_claude_output.txt"
REPORT_DATE = datetime.now().strftime("%Y-%m-%d")
PDF_OUTPUT_PATH = tmp_dir / f"trading_advisor_claude_report_{REPORT_DATE}.pdf"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# Defaults to Opus (most capable). For a cheaper/faster model, set CLAUDE_MODEL
# in .env to e.g. "claude-sonnet-5" or "claude-haiku-4-5".
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
REPORT_AUTHOR = "Bram-Jan Duits"

SELL_SIGNAL_TO_ADVICE = {
    "Recommend taking profit": "Sell",
    "Consider partial profit taking": "Sell partial",
    "Consider cutting losses": "Sell",
    "Review position; possible stop-loss": "Sell",
    "Consider selling to protect capital": "Sell",
    "Hold and monitor": "Hold",
}

ADVICE_COLORS = {
    "Buy": colors.HexColor("#1a7f37"),
    "Watch": colors.HexColor("#9a6700"),
    "Avoid": colors.HexColor("#8b1a1a"),
    "Sell": colors.HexColor("#8b1a1a"),
    "Sell partial": colors.HexColor("#9a6700"),
    "Hold": colors.HexColor("#1a5f9a"),
}

# --- Dutch translations for presentation only; underlying data/logic stays English ---
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
TYPE_NL = {"Stock": "Aandeel", "Crypto": "Crypto"}
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


def compute_advice(held: bool, sell_signal: str, score: int) -> str:
    if held:
        return SELL_SIGNAL_TO_ADVICE.get(sell_signal, "Hold")
    if score >= 65:
        return "Buy"
    if score >= 55:
        return "Watch"
    return "Avoid"


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


CURRENCY_SYMBOLS = {"EUR": "€", "USD": "$", "CHF": "CHF "}


def format_price(currency: str, price: Optional[float]) -> str:
    if price is None:
        return "n.v.t."
    symbol = CURRENCY_SYMBOLS.get(currency, f"{currency} ")
    return f"{symbol}{price:,.2f}"


def format_pct(value: Optional[float]) -> str:
    return f"{value:+.1f}%" if value is not None else "n.v.t."


def load_report() -> Dict:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Research report not found: {REPORT_PATH}")
    with open(REPORT_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_assets(report: Dict) -> List[Dict]:
    fx_rates = report.get("fx_rates", {})
    assets = []
    for asset in report.get("crypto_analysis", []) + report.get("stock_analysis", []):
        is_crypto = "change_24h_pct" in asset
        held = asset.get("held", False)
        sell_signal = asset.get("sell_signal", "")
        score = asset.get("score", 0)
        currency = asset.get("currency", "USD")
        assets.append({
            "type": "Crypto" if is_crypto else "Stock",
            "symbol": asset.get("symbol"),
            "name": asset.get("name"),
            "platform": asset.get("platform", "n/a"),
            "current_price": asset.get("current_price"),
            "currency": currency,
            "funding_advice": compute_funding_advice(currency, fx_rates),
            "change_recent_pct": asset.get("change_24h_pct", asset.get("change_pct")),
            "change_7d_pct": asset.get("change_7d_pct"),
            "momentum": asset.get("momentum", ""),
            "long_term_note": asset.get("long_term_note", ""),
            "risk": asset.get("risk_level", "unknown"),
            "score": score,
            "estimated_profit_pct": asset.get("estimated_profit_pct", 0.0),
            "estimated_cost_pct": asset.get("estimated_cost_pct", 0.0),
            "held": held,
            "quantity": asset.get("quantity"),
            "avg_price": asset.get("avg_price"),
            "unrealized_pct": asset.get("unrealized_pct"),
            "sell_signal": sell_signal,
            "advice": compute_advice(held, sell_signal, score),
        })
    return assets


def build_prompt(assets: List[Dict], headlines: List[Dict], fx_rates: Dict) -> str:
    eur_usd = fx_rates.get("EURUSD")
    eur_chf = fx_rates.get("EURCHF")
    lines = [
        "Je bent een warme, vriendelijke beleggingsadviseur die schrijft voor een "
        "particuliere belegger. De belegger houdt zijn geld voornamelijk in EUR aan, "
        "met een deel in Zwitserse frank (CHF) als reserve. Schrijf in het Nederlands, "
        "in een bemoedigende, prettig leesbare stijl (platte tekst, geen kopjes, geen "
        "markdown, geen opsommingstekens), verdeeld in 8-9 korte alinea's die in deze "
        "volgorde het volgende behandelen:\n"
        "1) Een warme, positieve opening over de algemene stemming op de markten.\n"
        "2) De beste koopkansen onder de aandelen en waarom, met aandacht voor "
        "kort (deze week) versus lang termijn (6 maanden) potentieel.\n"
        "3) Valuta en cryptocurrencies specifiek: vooruitzichten kort versus lang.\n"
        "4) Grondstoffen (goud, zilver, olie, landbouw/voedsel): wat ze doen en "
        "waarom ze vaak juist bewegen op geopolitiek, weer en vraag/aanbod nieuws.\n"
        "5) Een aparte alinea specifiek over welke valuta te gebruiken: leg uit dat "
        f"USD-genoteerde posities vanuit EUR gewisseld worden (huidige koers "
        f"1 EUR ≈ {eur_usd} USD), dat EUR-genoteerde posities (waaronder crypto via "
        f"Coinmerce) rechtstreeks in EUR kunnen, en bespreek in algemene termen "
        f"(zonder exacte actuele CPI-cijfers te verzinnen) waarom de Zwitserse frank "
        f"(huidige koers 1 EUR ≈ {eur_chf} CHF) historisch als inflatie-arme "
        "vluchthaven-valuta geldt en dus eerder als buffer dan als dagelijkse "
        "betaalvaluta te gebruiken is, terwijl eurozone-inflatie de koopkracht van "
        "EUR-tegoeden juist kan uithollen.\n"
        "6) Wat te vermijden is en waarom (risicofactoren).\n"
        "7) Een aparte alinea over bredere risico's en kansen: bespreek, uitsluitend "
        "gebaseerd op de onderstaande actuele nieuwskoppen (verzin geen concrete "
        "gebeurtenissen die er niet in staan), hoe zaken als oorlog/geopolitieke "
        "spanningen, natuurrampen/extreem weer, en positieve ontwikkelingen "
        "(bijvoorbeeld technologische doorbraken, sterke bedrijfsresultaten) de "
        "markten en met name grondstoffen kunnen raken. Blijf voorzichtig en "
        "algemeen als het nieuws geen directe link heeft.\n"
        "8) Hoe de recente geschiedenis (24u/7-daagse trend) dit beeld vormt.\n"
        "9) Een vriendelijke afsluiting die benadrukt dat dit educatief onderzoek "
        "is, geen financieel advies, en dat de lezer alles zelf moet verifiëren.\n\n"
        "Marktdata (symbool, naam, type, prijs, valuta, recente en 7-daagse "
        "verandering, momentum, langetermijnnotitie, risico, score, ons eigen "
        "Koop/Volg/Vermijd/Verkoop-advies, geschat rendement/kosten, platform):\n"
    ]
    for a in assets:
        lines.append(
            f"- {a['symbol']} ({a['name']}, {a['type']}): prijs={a['current_price']} "
            f"{a['currency']} recente_verandering={a['change_recent_pct']}% "
            f"7d_verandering={a['change_7d_pct']}% momentum={a['momentum']} "
            f"lange_termijn={a['long_term_note']} risico={a['risk']} "
            f"score={a['score']} advies={a['advice']} "
            f"geschat_rendement={a['estimated_profit_pct']}% "
            f"geschatte_kosten={a['estimated_cost_pct']}% platform={a['platform']}"
        )

    lines.append("\nActuele nieuwskoppen (titel — bron):")
    if headlines:
        for h in headlines[:10]:
            title = h.get("title", "")
            source = h.get("source", {}).get("name", "")
            lines.append(f"- {title} — {source}")
    else:
        lines.append("- (geen nieuwskoppen beschikbaar)")

    return "\n".join(lines)


def run_claude(prompt: str) -> str:
    if anthropic is None:
        raise ImportError("Install the Anthropic SDK with: python -m pip install anthropic")
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is required in .env to use Claude.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2500,
        system=(
            "Je bent een vriendelijke, toegankelijke beleggingsadviseur die in het "
            "Nederlands schrijft. Dit is educatief onderzoek, geen financieel advies."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()


def save_text_output(content: str) -> None:
    with open(TEXT_OUTPUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(content)
    logger.info(f"Claude advisor narrative saved to {TEXT_OUTPUT_PATH}")


def build_pdf(assets: List[Dict], narrative: str, headlines: List[Dict], fx_rates: Dict, generated_at: str) -> None:
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
        title="Beleggingsadvies Rapport", author=REPORT_AUTHOR, subject="Trading Advisor Report",
    )
    story = []

    story.append(Paragraph("Uw Vriendelijke Beleggingsadvies Rapport", title_style))
    story.append(Paragraph(
        f"Opgesteld door {escape(REPORT_AUTHOR)} &middot; Gegenereerd op "
        f"{escape(generated_at)} &middot; Educatief onderzoek, geen financieel advies",
        subtitle_style,
    ))

    story.append(Paragraph("Waar houdt dit rapport rekening mee?", h2))
    story.append(Paragraph(
        "Dit advies is opgesteld voor gebruik via <b>Degiro.nl</b> (aandelen en "
        "grondstoffen) en <b>Coinmerce</b> (cryptovaluta) — de platforms en "
        "beschikbaarheid kunnen per aanbieder verschillen, dus controleer altijd "
        "zelf of een positie daar daadwerkelijk verhandelbaar is.",
        body,
    ))
    story.append(Paragraph(
        "De scores en adviezen zijn gebaseerd op koersmomentum (recente en "
        "7-daagse verandering, volatiliteit en volume) per aandeel, grondstof en "
        "cryptovaluta.",
        body,
    ))
    story.append(Paragraph(
        "Daarnaast wegen we bredere omstandigheden mee: economische signalen uit "
        "actueel financieel nieuws, geopolitieke spanningen en oorlog, en "
        "(potentiële) natuurrampen of extreem weer voor zover die in het "
        "opgehaalde nieuws naar voren komen — we verzinnen geen gebeurtenissen "
        "die niet in de bronnen staan.",
        body,
    ))
    story.append(Paragraph(
        "Ook inflatie en valuta wegen mee: welke munt (EUR, USD of CHF) een "
        "positie vereist, de actuele wisselkoers, en het feit dat u vermogen "
        "aanhoudt in euro en Zwitserse frank — met de frank als beoogde "
        "inflatie-arme reserve.",
        body,
    ))
    story.append(Paragraph(
        "Dit blijft automatisch, heuristisch onderzoek gecombineerd met een "
        "AI-samenvatting: geen persoonlijk financieel advies en geen garantie "
        "voor toekomstige resultaten.",
        body,
    ))
    story.append(Spacer(1, 8))

    ranked = sorted(assets, key=lambda x: -x["score"])

    story.append(Paragraph("In één oogopslag", h2))
    table_data = [["Aandeel", "Type", "Valuta", "Prijs", "Recent", "7 dagen", "Advies", "Termijn"]]
    for a in ranked:
        term = "Kort & Lang" if a["score"] >= 65 else ("Lang" if a["score"] >= 55 else "-")
        table_data.append([
            f"{a['symbol']}\n{a['name']}",
            TYPE_NL.get(a["type"], a["type"]),
            a["currency"],
            format_price(a["currency"], a["current_price"]),
            format_pct(a["change_recent_pct"]),
            format_pct(a["change_7d_pct"]),
            ADVICE_NL.get(a["advice"], a["advice"]),
            term,
        ])

    tbl = Table(
        table_data,
        colWidths=[3.2 * cm, 2.1 * cm, 1.4 * cm, 2.1 * cm, 1.7 * cm, 1.7 * cm, 2.2 * cm, 2.0 * cm],
        repeatRows=1,
    )
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3d5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
    ]
    for i, a in enumerate(ranked, start=1):
        color = ADVICE_COLORS.get(a["advice"], colors.black)
        style_cmds.append(("TEXTCOLOR", (6, i), (6, i), color))
        style_cmds.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))
    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Vooruitzicht van deze week", h2))
    for para in narrative.split("\n\n"):
        para = para.strip()
        if para:
            story.append(Paragraph(escape(para), body))

    eur_usd = fx_rates.get("EURUSD")
    eur_chf = fx_rates.get("EURCHF")
    story.append(Paragraph("Welke valuta gebruiken?", h2))
    story.append(Paragraph(
        f"Actuele koersen: 1 EUR ≈ {eur_usd:.3f} USD, 1 EUR ≈ {eur_chf:.3f} CHF."
        if eur_usd and eur_chf else "Actuele wisselkoersen konden niet worden opgehaald.",
        body,
    ))
    story.append(Paragraph(
        "Voor posities in EUR (waaronder crypto via Coinmerce) betaalt u rechtstreeks "
        "in EUR, zonder wisselkosten. Voor USD-genoteerde aandelen wisselt u vanuit EUR. "
        "Uw Zwitserse frank (CHF) kunt u het beste als reserve aanhouden: de frank geldt "
        "van oudsher als een inflatie-arme vluchthavenvaluta, terwijl de koopkracht van "
        "EUR-tegoeden sterker onder druk kan staan bij hogere eurozone-inflatie. Wissel "
        "CHF dus liever niet routinematig om voor kleine aankopen — bewaar die reserve "
        "voor grotere posities of onrustige markten.",
        body,
    ))

    buys = [a for a in ranked if a["advice"] == "Buy"]
    if buys:
        story.append(Paragraph("Koopadvies", h2))
        for a in buys:
            story.append(Paragraph(
                f"<b>{escape(a['symbol'])} — {escape(a['name'])}</b> "
                f"({escape(TYPE_NL.get(a['type'], a['type']))}, {escape(a['platform'])}): "
                f"{escape(MOMENTUM_NL.get(a['momentum'], a['momentum']))}, "
                f"vooruitzicht lange termijn: "
                f"{escape(LONG_TERM_NOTE_NL.get(a['long_term_note'], a['long_term_note']))}. "
                f"Geschat winstpotentieel {a['estimated_profit_pct']:.2f}% "
                f"(geschatte kosten {a['estimated_cost_pct']:.2f}%). "
                f"Risico: {escape(RISK_NL.get(a['risk'], a['risk']))}. "
                f"Valuta: {escape(a['funding_advice'])}",
                body,
            ))

    watch = [a for a in ranked if a["advice"] == "Watch"]
    if watch:
        story.append(Paragraph("Om in de gaten te houden", h2))
        for a in watch:
            story.append(Paragraph(
                f"<b>{escape(a['symbol'])} — {escape(a['name'])}</b> "
                f"({escape(TYPE_NL.get(a['type'], a['type']))}): "
                f"{escape(MOMENTUM_NL.get(a['momentum'], a['momentum']))}, "
                f"lange termijn: "
                f"{escape(LONG_TERM_NOTE_NL.get(a['long_term_note'], a['long_term_note']))}. "
                f"Risico: {escape(RISK_NL.get(a['risk'], a['risk']))}.",
                body,
            ))

    holdings = [a for a in ranked if a["held"]]
    if holdings:
        story.append(Paragraph("Uw Huidige Posities", h2))
        for a in holdings:
            story.append(Paragraph(
                f"<b>{escape(a['symbol'])} — {escape(a['name'])}</b>: "
                f"{escape(SELL_SIGNAL_NL.get(a['sell_signal'], a['sell_signal']))} "
                f"(ongerealiseerd: {format_pct(a['unrealized_pct'])}).",
                body,
            ))

    if headlines:
        story.append(Paragraph("Actueel Nieuws Meegewogen in dit Rapport", h2))
        for h in headlines[:10]:
            title = h.get("title", "")
            source = h.get("source", {}).get("name", "")
            story.append(Paragraph(f"&bull; {escape(title)} — <i>{escape(source)}</i>", body))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Dit rapport is gegenereerd op basis van geautomatiseerde onderzoeksheuristieken "
        "en een AI-verhaal, uitsluitend voor educatieve doeleinden. Dit is geen financieel "
        "advies. Controleer altijd zelf actuele prijzen, liquiditeit, kosten en "
        "platformbeschikbaarheid, en houd rekening met uw eigen risicobereidheid voordat "
        "u handelt.",
        small,
    ))

    doc.build(story)
    logger.info(f"Vriendelijk PDF-rapport opgeslagen op {PDF_OUTPUT_PATH}")


def main() -> None:
    try:
        report = load_report()
    except Exception as exc:
        logger.error(f"Failed to load research report: {exc}")
        return

    assets = build_assets(report)
    headlines = report.get("news", [])
    fx_rates = report.get("fx_rates", {})
    prompt = build_prompt(assets, headlines, fx_rates)
    try:
        narrative = run_claude(prompt)
    except Exception as exc:
        logger.error(f"Claude request failed: {exc}")
        return

    save_text_output(narrative)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        build_pdf(assets, narrative, headlines, fx_rates, generated_at)
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}")
        return

    print(narrative)
    print(f"\nPDF report saved to: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    main()

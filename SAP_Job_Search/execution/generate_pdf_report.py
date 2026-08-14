#!/usr/bin/env python3
"""
Renders the SAP job search findings (Belgium & Netherlands) as a PDF report.

Reads no external input — the findings below are a snapshot transcribed from
`SAP_Job_Search/findings/sap_jobs_be_nl_<date>.md`. Re-run after updating that
markdown file with a fresh search pass to regenerate the PDF for the new date.
"""

import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, ListFlowable, ListItem
)

REPORT_DATE = "2026-08-06"
root_dir = Path(__file__).parent.parent
findings_dir = root_dir / "findings"
findings_dir.mkdir(exist_ok=True, parents=True)
PDF_OUTPUT_PATH = findings_dir / f"sap_jobs_be_nl_{REPORT_DATE}.pdf"

# Role, Company, Location, Posted — filtered to unique roles posted within the last 7
# days (from a live LinkedIn search on REPORT_DATE), most-recent first.
NL_ROLES = [
    ["SAP Integration Specialist", "Alliander", "Arnhem", "8 min ago (6 Aug)"],
    ["SAP S/4HANA Roadmap & Business Transformation Advisor", "Accenture NL", "Amsterdam", "15 hrs ago (5 Aug)"],
    ["SAP Solution Architect", "Brabant Water N.V.", "'s-Hertogenbosch", "16 hrs ago (5 Aug)"],
    ["SAP-ontwikkelaar", "myBrand | Conclusion", "Maarssen", "18 hrs ago (5 Aug)"],
    ["SAP/BTP Development Specialist", "Nyrstar", "Budel", "20 hrs ago (5 Aug)"],
    ["SAP CAP Developer", "delaware the Netherlands", "Den Bosch", "1 day ago (5 Aug)"],
    ["SAP S/4HANA Data Transformation Advisor", "Accenture NL", "Amsterdam", "2 days ago (4 Aug)"],
    ["Manager SAP S/4HANA Sales and Distribution", "Deloitte", "Amsterdam", "2 days ago (4 Aug)"],
    ["SAP Production Consultant", "NTT DATA Business Solutions", "'s-Hertogenbosch", "2 days ago (4 Aug)"],
    ["SAP Integration Consultant", "Accenture NL", "Amsterdam", "4 days ago (2 Aug)"],
    ["SAP Sales Distribution Consultant (SD/OTC)", "Accenture NL", "Amsterdam", "4 days ago (2 Aug)"],
    ["SAP Development Architect & Team Lead", "Accenture NL", "Amsterdam", "5 days ago (1 Aug)"],
    ["SAP Architect – NL", "Capgemini", "Utrecht", "5 days ago (1 Aug)"],
    ["SAP Manufacturing Manager", "Accenture NL", "Amsterdam", "5 days ago (1 Aug)"],
    ["SAP S/4 Digital EAM Consultant", "Accenture NL", "Amsterdam", "5 days ago (1 Aug)"],
    ["SAP Security Lead", "Scandinavian Tobacco Group", "Waalre", "5 days ago (1 Aug)"],
    ["Super User SAP", "Scania Production & Logistics NL", "Hasselt (Overijssel)", "5 days ago (1 Aug)"],
    ["SAP Group Reporting & Public Cloud", "RED Global", "South Holland", "5 days ago (1 Aug)"],
    ["SAP developer", "Stedin", "Delft", "6 days ago (31 Jul)"],
    ["Technical Application manager", "Panda International", "Bilthoven", "6 days ago (31 Jul)"],
    ["Consultant SAP EAM", "Deloitte", "Amsterdam", "6 days ago (31 Jul)"],
    ["SAP Sourcing & Procurement Consultant", "Accenture NL", "Amsterdam", "6 days ago (31 Jul)"],
    ["SAP ABAP Developer", "Stedin", "Delft", "1 week ago (30 Jul)"],
    ["SAP C4C consultant", "Stedin", "Rotterdam", "1 week ago (30 Jul)"],
    ["AI Tech Consultant (ERP/SAP)", "BCG Platinion", "Amsterdam", "1 week ago (30 Jul)"],
    ["Lead AI Tech Architect (ERP/SAP)", "BCG Platinion", "Amsterdam", "1 week ago (30 Jul)"],
    ["Senior AI Tech Architect (ERP/SAP)", "BCG Platinion", "Amsterdam", "1 week ago (30 Jul)"],
    ["Senior SAP Developer", "vidaXL", "Venlo", "1 week ago (30 Jul)"],
    ["SAP Developer", "Applied Medical", "Amersfoort", "1 week ago (30 Jul)"],
    ["SAP Treasury Risk Management", "Accenture NL", "Amsterdam", "1 week ago (30 Jul)"],
]

BE_ROLES = [
    ["SAP Analyst", "ThoughtLabs Belgium", "Brussels", "55 min ago (6 Aug)"],
    ["SAP PP/QM", "JoBBsquare België", "Antwerp", "8 hrs ago (6 Aug)"],
    ["SAP Functioneel Analyst", "Madison Recruitment", "Aalst", "13 hrs ago (5 Aug)"],
    ["SAP GTS Consultant", "Deloitte", "Zaventem", "16 hrs ago (5 Aug)"],
    ["SAP TM Consultant", "Deloitte", "Zaventem", "18 hrs ago (5 Aug)"],
    ["System Exploitation Engineer – SAP BC Member", "Sibelga", "Brussels", "1 day ago (5 Aug)"],
    ["Functioneel SAP-analist", "Aures", "Wingene", "1 day ago (5 Aug)"],
    ["SAP Enterprise Architect", "Robert Half (client role)", "Ghent", "1 day ago (5 Aug)"],
    ["SAP BDC Lead", "KPMG Belgium", "Zaventem", "1 day ago (5 Aug)"],
    ["Senior SAP Sales & Distribution Consultant", "delaware BeLux", "Ghent", "1 day ago (5 Aug)"],
    ["Responsable Fonctionnel SAP Quality / WMS", "Safran", "Liège", "2 days ago (4 Aug)"],
    ["Responsable Fonctionnel SAP Finance", "Safran", "Liège", "2 days ago (4 Aug)"],
    ["SAP Architect (SD/MM)", "Amon", "Kaprijke", "2 days ago (4 Aug)"],
    ["SAP FICO Consultant", "Deloitte", "Zaventem", "2 days ago (4 Aug)"],
    ["SAP Business One Consultant", "Amaris Consulting", "Herstal", "2 days ago (4 Aug)"],
    ["SAP Application Security Consultant", "BDO Belgium", "Zaventem", "2 days ago (4 Aug)"],
    ["SAP Global Trade Services Consultant", "delaware BeLux", "Ghent", "2 days ago (4 Aug)"],
    ["SAP Enterprise Architect", "KPMG Belgium", "Zaventem", "3 days ago (3 Aug)"],
    ["SAP Archiving & ILM Manager", "Deloitte", "Zaventem", "3 days ago (3 Aug)"],
    ["SAP EWM/WM Consultant", "Accenture Belgium", "Brussels", "4 days ago (2 Aug)"],
    ["SAP S/4HANA Functional Analyst & Developer", "Talan", "Brussels", "4 days ago (2 Aug)"],
    ["SAP Developer", "Kingfisher Recruitment", "Oud-Turnhout", "5 days ago (1 Aug)"],
    ["SAP Solution Architect", "Sopra Steria", "Brussels", "5 days ago (1 Aug)"],
    ["SAP PS Senior Manager", "Accenture Belgium", "Brussels", "5 days ago (1 Aug)"],
    ["Functional Analyst SAP Logistics (Sr)", "John Cockerill", "Seraing", "5 days ago (1 Aug)"],
    ["SAP Supply Chain Planning Specialist", "Deloitte", "Zaventem", "6 days ago (31 Jul)"],
    ["SAP Specialist", "Indaver", "Beveren", "6 days ago (31 Jul)"],
    ["SAP Sales", "Match Profiler", "Kaprijke", "1 week ago (30 Jul)"],
    ["Lead Consultant – SAP Manufacturing", "Emixa", "Antwerp", "1 week ago (30 Jul)"],
    ["SAP Solutions Specialist", "Deloitte", "Zaventem", "1 week ago (30 Jul)"],
    ["SAP Team Lead", "Crop's", "West Flanders", "1 week ago (30 Jul)"],
    ["SAP-PP & MES Consultant", "stow Group", "Spiere-Helkijn", "1 week ago (30 Jul)"],
    ["Consultant(e) SAP S/4HANA (M/F)", "mc2i", "Brussels", "1 week ago (30 Jul)"],
    ["Solution Architect SAP", "Madison Recruitment", "Genk", "1 week ago (30 Jul)"],
    ["SAP PP Consultant", "delaware BeLux", "Flemish Region", "1 week ago (30 Jul)"],
]

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "TitleCustom", parent=styles["Title"], alignment=TA_CENTER, fontSize=18,
    spaceAfter=4,
)
subtitle_style = ParagraphStyle(
    "SubtitleCustom", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10,
    textColor=colors.grey, spaceAfter=16,
)
h2_style = ParagraphStyle(
    "H2Custom", parent=styles["Heading2"], spaceBefore=16, spaceAfter=6,
    textColor=colors.HexColor("#1a3a5c"),
)
body_style = ParagraphStyle("BodyCustom", parent=styles["Normal"], fontSize=9, leading=12)
cell_style = ParagraphStyle("CellCustom", parent=styles["Normal"], fontSize=8, leading=10)
note_style = ParagraphStyle(
    "NoteCustom", parent=styles["Normal"], fontSize=9, leading=13, spaceAfter=6,
)

TABLE_HEADER_BG = colors.HexColor("#1a3a5c")
TABLE_ROW_BG = colors.HexColor("#f2f6fa")


def P(text: str) -> Paragraph:
    return Paragraph(text, cell_style)


def make_table(header, rows, col_widths):
    data = [[P(f"<b>{h}</b>") for h in header]] + [
        [P(str(cell)) for cell in row] for row in rows
    ]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d6e3")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TABLE_ROW_BG]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_OUTPUT_PATH), pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
    )
    story = []

    story.append(Paragraph("SAP Job Search — België &amp; Nederland", title_style))
    story.append(Paragraph(
        f"Findings gathered {REPORT_DATE} &mdash; re-verify contact details and postings "
        "before relying on them", subtitle_style,
    ))

    # 1. Job boards
    story.append(Paragraph("1. Open job board sites", h2_style))
    story.append(make_table(
        ["Site", "Country", "URL", "Posting-date signal"],
        [
            ["LinkedIn Jobs", "Both", "linkedin.com/jobs", "Exact \"Posted X hours/days ago\" — most reliable"],
            ["Indeed", "BE", "be.indeed.com", "\"Posted X days ago\" shown per listing"],
            ["Indeed", "NL", "nl.indeed.com", "Same as above"],
            ["StepStone", "BE", "stepstone.be/jobs/consultant-sap", "\"geplaatst op\" date; JS-heavy — browse manually"],
            ["Glassdoor", "Both", "glassdoor.com", "Relative posted date shown"],
            ["Jobat", "BE", "jobat.be", "Belgian IT-focused board (De Persgroep)"],
            ["VDAB", "BE", "vdab.be", "Public employment service"],
            ["Nationale Vacaturebank", "NL", "nationalevacaturebank.nl", "Dutch general board"],
            ["ICTergezocht", "NL", "ictergezocht.nl", "IT-focused"],
            ["eXpatJobs", "NL", "netherlands.expatjobs.eu", "English-language, expat-oriented"],
            ["Eursap (SAP-only)", "Both", "eursap.eu/sap-recruitment/…", "See live listings below"],
            ["SAP Careers", "Both", "careers.sap.com", "SAP SE's own in-house vacancies"],
        ],
        [3.3 * cm, 1.6 * cm, 5.6 * cm, 6.0 * cm],
    ))

    # 2. Currently open roles — Netherlands
    story.append(Paragraph("2. Currently open SAP roles — posted within the last 7 days", h2_style))
    story.append(Paragraph(
        "First pass only surfaced 3 roles because it checked a thin specialist feed. "
        "Re-run against LinkedIn/Indeed directly and filtered to unique roles posted in "
        "the last 7 days, sorted most-recent first.", body_style,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Netherlands (via LinkedIn)", styles["Heading3"]))
    story.append(make_table(
        ["Role", "Company", "Location", "Posted"],
        NL_ROLES,
        [6.2 * cm, 4.5 * cm, 3.0 * cm, 3.0 * cm],
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Belgium (via LinkedIn)", styles["Heading3"]))
    story.append(make_table(
        ["Role", "Company", "Location", "Posted"],
        BE_ROLES,
        [6.2 * cm, 4.5 * cm, 3.0 * cm, 3.0 * cm],
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Also currently posted on Indeed NL/BE (dates less reliable, several look like "
        "evergreen listings): NTT DATA Business Solutions and Capgemini Sogeti each have "
        "5+ open SAP roles in Den Bosch and Diegem respectively; see the findings markdown "
        "for the full list.", note_style,
    ))

    # 3. Live Eursap vacancies
    story.append(Paragraph("3. Live vacancies seen on Eursap (SAP-only recruiter feed)", h2_style))
    story.append(Paragraph(
        "Eursap's BE and NL pages currently surface the same central feed &mdash; filter "
        "by location once you register/apply.", body_style,
    ))
    story.append(Spacer(1, 4))
    story.append(make_table(
        ["Role", "Job ID", "Location", "Type", "Rate / Salary"],
        [
            ["SAP S/4HANA Finance Consultant", "35123", "France, remote", "Contract", "Market rates"],
            ["SAP BTP Techno-Functional Consultant", "35124", "France, remote", "Contract", "Market rates"],
            ["SAP Project Manager / Trainer", "34811", "Remote", "Permanent", "€80,000–€156,000 gross/yr + equity"],
        ],
        [6.0 * cm, 1.8 * cm, 3.2 * cm, 2.2 * cm, 3.3 * cm],
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Note: these three listings show a <b>start date</b> (5 Oct 2026 / 1 Sep 2026), "
        "not a posting date, and none is BE/NL-located specifically &mdash; call the local "
        "office directly to ask what is currently open.", note_style,
    ))

    # 4. Recruitment partners
    story.append(Paragraph("4. Recruitment partners / agencies — contacts", h2_style))
    story.append(make_table(
        ["Agency", "Specialism", "Belgium contact", "Netherlands contact"],
        [
            ["Eursap", "SAP-only specialist", "+32 (0)2 808 5964", "+31 (0)20 890 8064"],
            ["Michael Page", "Generalist incl. IT/SAP",
             "Brussels +32 (0)2 509 4545 — Marsveldplein 5, 1050 Ixelles",
             "Amsterdam +31 (0)20 578 9444 — Strawinskylaan 421, 1077 XX"],
            ["Hays", "Generalist incl. IT/SAP", "Not confirmed this pass — see hays.be",
             "Amsterdam +31 (0)20 363 0310 — Rijnsburgstraat 9-11, 1059 AT"],
            ["Robert Half", "Generalist incl. IT/SAP", "+32 3 241 14 28",
             "Amsterdam — Transformatorweg 82, 1014 AK (no direct line found)"],
            ["Approach People Recruitment", "Generalist, Brussels-based, int'l",
             "Brussels office; group line +353 1 400 3500", "—"],
            ["GS-IT Recruitment", "SAP specialist, pan-European", "Contact form only (gs-it-recruitment.eu)",
             "Contact form only"],
            ["YER", "Dutch staffing, 10 NL branches", "—", "Branch locator on yer.nl"],
        ],
        [3.4 * cm, 3.4 * cm, 4.6 * cm, 5.1 * cm],
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Email: info@eursap.eu / cvs@eursap.eu. Not yet confirmed with a direct phone "
        "number this pass: Hays Belgium, GS-IT Recruitment, YER branch numbers, Yacht, "
        "USG Professionals / Impellam, Randstad Professionals SAP desk.", note_style,
    ))

    # 5. Notes on posting dates
    story.append(Paragraph("5. On job-posting dates", h2_style))
    bullets = ListFlowable(
        [
            ListItem(Paragraph(
                "LinkedIn is the most reliable signal: an exact &ldquo;posted X "
                "hours/minutes/days ago&rdquo; per listing &mdash; the tables above are "
                "built directly from it.", body_style)),
            ListItem(Paragraph(
                "Indeed also shows a posted date, but several listings (e.g. large NTT "
                "DATA batches) showed a flat &ldquo;Posted: 6 August 2026&rdquo; for every "
                "result, which looks more like a default freshness label than a true post "
                "date &mdash; treat Indeed dates as indicative, LinkedIn's as more "
                "trustworthy.", body_style)),
            ListItem(Paragraph(
                "Specialist recruiter sites (Eursap) show a contract/permanent start date "
                "or an internal Job ID, not the date the ad went live &mdash; don't read "
                "those as posting dates.", body_style)),
            ListItem(Paragraph(
                "Glassdoor and Jobat blocked automated fetching this pass (HTTP 403 / "
                "fetch failure) &mdash; browse those two directly in a browser.", body_style)),
            ListItem(Paragraph(
                "StepStone shows a &ldquo;geplaatst op&rdquo; (posted on) date but its "
                "listing pages timed out on automated fetch (JS-rendered / "
                "bot-resistant) &mdash; check manually in a browser.", body_style)),
        ],
        bulletType="bullet", start="circle", leftIndent=14,
    )
    story.append(bullets)

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} &mdash; source markdown: "
        "SAP_Job_Search/findings/sap_jobs_be_nl_2026-08-06.md", subtitle_style,
    ))

    doc.build(story)
    print(f"PDF report saved to: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()

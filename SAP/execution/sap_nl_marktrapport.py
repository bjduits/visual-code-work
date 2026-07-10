#!/usr/bin/env python3
"""
Render the SAP Netherlands market-map report (Dutch) as a PDF.

The underlying research (companies, tiers, rates, product landscape, news)
was gathered manually via web research and is embedded below as structured
data. Confidence levels are kept explicit throughout since per-company
market share, financial health, and exact product footprints are not
reliably verifiable via public sources.
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
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak, ListFlowable, ListItem
)

root_dir = Path(__file__).parent.parent
tmp_dir = root_dir / ".tmp"
tmp_dir.mkdir(exist_ok=True)

REPORT_DATE = datetime.now().strftime("%Y-%m-%d")
PDF_OUTPUT_PATH = tmp_dir / f"sap_nl_marktrapport_{REPORT_DATE}.pdf"
REPORT_AUTHOR = "Bram-Jan Duits"

NAVY = colors.HexColor("#1a3d5c")
BLUE = colors.HexColor("#0070C0")
GREY = colors.grey
LIGHT_ROW = colors.HexColor("#f5f7fa")

CONF_COLOR = {
    "Hoog": colors.HexColor("#1a7f37"),
    "Gemiddeld": colors.HexColor("#9a6700"),
    "Laag": colors.HexColor("#8b1a1a"),
}

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

EINDKLANTEN = [
    ("Shell", "Energie", "Grootschalige SAP ECC/S4-gebruiker wereldwijd; NL (Den Haag) is een belangrijke hub. Details S/4-programma niet gevonden.", "Gemiddeld"),
    ("Heineken", "Brouwerij (Amsterdam)", "SAP-gebruiker, ca. 46.000 medewerkers.", "Hoog"),
    ("KLM / Air France-KLM", "Luchtvaart", "Consolideert naar één gedeelde SAP-omgeving; S/4HANA-migratie in voorbereiding; werft actief SAP-consultants.", "Hoog"),
    ("Philips", "Health tech (Amsterdam)", "SAP-gebruiker, ca. 82.000 medewerkers, $19 mrd omzet.", "Hoog (als klant) / Laag (details)"),
    ("ASML", "Halfgeleiderapparatuur (Veldhoven)", "Bevestigde SAP-klant; exacte modules niet gevonden.", "Gemiddeld"),
    ("Ahold Delhaize / ADUSA", "Retail", "Actief meerjarig SAP S/4HANA-transformatietraject ('Project Catalyst'); werft 'Functional Application Owner - SAP S/4HANA'.", "Hoog"),
    ("DSM-Firmenich (Twilmij)", "Voeding/chemie", "Onderdeel Twilmij draait SAP S/4HANA Cloud Public Edition, two-tier ERP-model.", "Hoog (voor Twilmij)"),
    ("Unilever (Benelux)", "FMCG", "Gebruikt SAP S/4HANA EWM + SAP CPG-add-on voor logistieke optimalisatie.", "Hoog"),
    ("Rabobank", "Bankwezen (Utrecht)", "Gemigreerd naar SAP S/4HANA Cloud (public, Azure) via 'OneFinance'; implementatiepartner Cognizant; breidt SAP BTP uit voor 'clean core'-extensies.", "Hoog"),
    ("Schiphol Group", "Luchthaven/infra", "HR gemoderniseerd naar SAP SuccessFactors (Employee Central + payroll) met EPI-USE Labs, Eviden, McCoy & Partners.", "Hoog"),
    ("PostNL", "Logistiek/post", "Gemigreerd van on-prem SAP HCM naar SAP SuccessFactors EC + payroll; 500.000 medewerkersdossiers in 20 weken.", "Hoog"),
    ("AkzoNobel", "Chemie/verf (Amsterdam)", "SAP-gebruiker, ca. 36.000 medewerkers, $12 mrd omzet.", "Hoog (als klant) / Laag (details)"),
    ("FrieslandCampina", "Zuivelcoöperatie", "SAP-gebruiker, ca. 24.000 medewerkers.", "Hoog"),
    ("Signify (ex-Philips Lighting)", "Verlichting", "SAP-gebruiker, ca. 37.000 medewerkers, $7,9 mrd omzet.", "Hoog"),
    ("Nouryon", "Specialty chemicals", "SAP-gebruiker, ca. 5.200 medewerkers.", "Hoog"),
    ("Louis Dreyfus Company", "Agrogrondstoffen (Rotterdam)", "SAP-gebruiker, ca. 18.000 medewerkers, $50 mrd omzet.", "Hoog"),
    ("Ministerie van Defensie", "Publieke sector", "SAP-gebruiker, ca. 31.000 medewerkers; scope onbekend.", "Hoog (als klant) / Laag (scope)"),
]

EINDKLANTEN_LETOP = (
    "Let op — twee namen die vaak in dit rijtje opduiken maar hier bewust zijn gecorrigeerd: "
    "<b>Vopak</b> is géén actieve SAP-klant meer — het bedrijf stapte over van JD Edwards naar "
    "<b>Oracle Cloud ERP/Fusion</b> (2022) en gebruikt Workday voor HR. <b>ING</b> kon dit onderzoek "
    "niet bevestigen als SAP-gebruiker; geen bewijs gevonden in beide richtingen — niet aannemen zonder "
    "verdere verificatie. De totale markt is groter dan deze steekproef: dataleveranciers noemen "
    "ca. 2.100-2.250 bedrijven met SAP in Nederland, waarvan ca. 283 op S/4HANA — bovenstaande lijst "
    "is een geverifieerde selectie, geen volledige telling."
)

EINDKLANTEN_UITGEBREID = [
    ("DAF Trucks N.V.", "Industrie", "SAP MRS (Maintenance & Repair Scheduling) voor technische dienst, live sinds 2019.", "Gemiddeld"),
    ("Damen Shipyards Group", "Industrie", "Migreert naar SAP S/4HANA, gehost door TCS op AWS.", "Gemiddeld"),
    ("Grolsche Bierbrouwerij (Grolsch)", "Industrie", "SAP R/3 ERP, geïntegreerd met ProLeit MES op de brouwerijvloer.", "Gemiddeld"),
    ("Nedschroef Machinery", "Industrie", "SAP Sales Cloud voor klant-/contractbeheer.", "Gemiddeld"),
    ("Flora Food Group (ex-Upfield)", "Industrie", "SAP HANA/ERP, master-data-integratie met douanesysteem.", "Gemiddeld"),
    ("Tata Steel Nederland (IJmuiden)", "Industrie", "Vermeld als gebruiker SAP ERP/Plant Maintenance.", "Laag"),
    ("Stellantis N.V. (HQ Amsterdam)", "Industrie", "SAP-gebruiker (272k medewerkers wereldwijd).", "Laag"),
    ("ASM International", "Industrie", "SAP S/4HANA-gebruiker.", "Laag"),
    ("FineField (Limburg)", "Industrie", "Live sinds okt 2024 op SAP S/4HANA Cloud Public Edition via GROW with SAP, partner Scheer Nederland.", "Hoog"),
    ("Yanmar Europe (Almere)", "Industrie", "SAP S/4HANA Cloud, partner Quinso; SAP Gold 'Best of Customer Success' 2021.", "Hoog"),
    ("Jumbo Supermarkten", "Retail", "Migratie van legacy (Super de Boer) SAP naar SAP S/4HANA.", "Hoog"),
    ("Action", "Retail", "SAP EWM, SAP Ariba, meerdere retailmodules via Ctac.", "Hoog"),
    ("IKEA Netherlands", "Retail", "SAP S/4HANA voor ERP Financial (2020), gefaseerde uitrol finance/inkoop/logistiek met Syniti.", "Gemiddeld"),
    ("Sligro Food Group", "Retail", "SAP Retail-omgeving (myBrand-hosting) + SAP Commerce Cloud voor foodservice-platform.", "Hoog"),
    ("Maxeda DIY Group (Praxis/Formido)", "Retail", "Digitale kern vernieuwd met SAP S/4HANA (Capgemini-case).", "Hoog"),
    ("Louwman (autodealergroep)", "Retail", "RISE with SAP; SAP PI gemigreerd naar SAP Integration Suite (BTP).", "Hoog"),
    ("ABN AMRO", "Financieel", "SAP FI/CO, SAP Ariba supplier network, roadmap ECC naar S/4HANA.", "Gemiddeld"),
    ("TMF Group (Amsterdam)", "Financieel", "SAP Business One via partner 'be one solutions' voor ERP-lokalisatie bij klanten.", "Gemiddeld"),
    ("Finalise", "Financieel", "SAP S/4HANA-gebruiker (kleine financiële dienstverlener).", "Laag"),
    ("Achmea", "Verzekeringen", "SAP S/4HANA + BTP-kernvernieuwing; eerste grote SAP-klant die volledige on-prem SAP-landschap naar Azure cloud verhuisde; SecurityBridge voor SAP-compliance.", "Hoog"),
    ("NN Group (Nationale-Nederlanden)", "Verzekeringen", "SAP ERP incl. FS-PM (pensioenmodule), SAP-landschap gemigreerd naar AWS via Lemongrass.", "Gemiddeld"),
    ("Amsterdam UMC (AMC)", "Zorg", "Volledig SAP ERP: Finance & Control, Inkoop, Logistiek, Facilities, HR.", "Hoog"),
    ("UMCG", "Zorg", "Eerste ziekenhuis op SAP S/4HANA-versie van ERP4HC-template (begin 2021).", "Gemiddeld"),
    ("UMC Utrecht", "Zorg", "SAP SRM voor digitaal bestellen/contractbeheer.", "Gemiddeld"),
    ("Zuyderland Medisch Centrum", "Zorg", "SAP-geïntegreerde beeldbelmodule (Enovation Zaurus).", "Gemiddeld"),
    ("TenneT", "Energie", "SAP S/4HANA-gebruiker.", "Laag"),
    ("Gasunie", "Energie", "SAP S/4HANA live sinds okt 2024 ('project Max', greenfield big-bang, met Deloitte).", "Hoog"),
    ("Enexis", "Energie", "SAP S/4HANA-modernisering met Accenture.", "Hoog"),
    ("Stedin", "Energie", "SAP Ariba-implementatie met partner delaware.", "Hoog"),
    ("Eneco", "Energie", "SAP S/4HANA + Central Finance (PwC); eerste klant wereldwijd die on-prem SAP PI naar SAP Cloud Integration verhuisde (2018).", "Hoog"),
    ("Vitens", "Energie", "SAP S/4HANA Utilities + SAP Service Cloud, transformatie sinds 2018.", "Hoog"),
    ("NS (Nederlandse Spoorwegen)", "Logistiek", "Gefragmenteerd ERP-landschap gemigreerd naar één SAP S/4HANA-omgeving.", "Gemiddeld"),
    ("ProRail", "Logistiek", "Een van NL's eerste greenfield SAP S/4HANA-implementaties (met Accenture); SAP Silver Quality Award 2019.", "Hoog"),
    ("Havenbedrijf Rotterdam", "Logistiek", "Overstap naar SAP Cloud ERP/S/4HANA Cloud, ondersteund door myBrand.", "Gemiddeld"),
    ("Workrate (Amsterdam)", "Logistiek", "SAP Business ByDesign via NTT DATA Business Solutions.", "Gemiddeld"),
    ("Rijkswaterstaat / Ministerie van I&W", "Overheid", "Grootste SAP S/4HANA-gebruiker binnen NL-overheid (4.500+ gebruikers), Atos als hosting-/beheerpartner.", "Gemiddeld"),
    ("Belastingdienst", "Overheid", "SAP Ariba voor inkoop/aanbesteding; interne FI/CO/PSM-modules.", "Gemiddeld"),
    ("Kadaster", "Overheid", "Bevestigd SAP-gebruiker; 'Taskforce SAP' (2014) en bevindingen SAP-beveiligingsaudit.", "Gemiddeld"),
    ("Provincie Utrecht", "Overheid", "SAP ERP live sinds jan 2016 (Finance & Projects, Sales & Procurement).", "Gemiddeld"),
    ("Provincie Noord-Brabant", "Overheid", "SAP Grants Management + SAP S/4HANA (vervangt SAP ECC).", "Hoog"),
    ("Provincie Noord-Holland", "Overheid", "SAP-omgeving, hosting/beheer door myBrand.", "Gemiddeld"),
    ("Gemeente Stein", "Overheid", "Overgestapt naar iFinanciën (PinkRoccade), gebaseerd op SAP S/4HANA, cloud-hosted.", "Gemiddeld"),
    ("KPN", "Telecom", "Intern SAP ERP (biedt ook SAP managed services aan 30+ NL-organisaties); SAP-geïntegreerde retail-scanoplossing.", "Gemiddeld"),
    ("Heijmans", "Bouw", "SAP Cloud for Customer (C4C) voor Vastgoed & Wonen-divisies.", "Hoog"),
    ("BAM Infra Nederland (Royal BAM Group)", "Bouw", "SAP S/4HANA voor finance/projectadministratie, Financial Shared Service Center.", "Hoog"),
    ("Dura Vermeer", "Bouw", "SAP LeanIX voor enterprise-architectuurbeheer, uitgerold 2024.", "Hoog"),
    ("Royal Agrifirm Group", "Agrifood", "Supply chain/asset management gestandaardiseerd op SAP S/4HANA (Capgemini).", "Hoog"),
    ("White Fields", "Agrifood", "SAP Cloud ERP geïmplementeerd in 3 maanden met Quinso; onderdeel nationale SAP MKB-campagne.", "Gemiddeld"),
    ("Koninklijke Cosun", "Agrifood", "Vacature 'Applicatiebeheerder SAP' bevestigt gebruik.", "Gemiddeld"),
    ("President Safety", "Agrifood", "SAP S/4HANA Public Cloud met Quinso, Computable Awards 2026-inzending.", "Hoog"),
    ("JDE Peet's", "Agrifood", "SAP Concur (T&E, ~40 markten, 10+ jaar) + SAP SuccessFactors Employee Central.", "Hoog"),
    ("Booking.com", "Technologie", "SAP S/4HANA-gebruiker.", "Laag"),
    ("Adevinta N.V. (Marktplaats)", "Technologie", "SAP S/4HANA-gebruiker.", "Laag"),
    ("TomTom", "Technologie", "RISE with SAP → S/4HANA, 'big bang'-livegang jan 2024.", "Hoog"),
    ("Leaseweb", "Technologie", "SAP-oplossingen geïmplementeerd (jan 2025, vakpers).", "Laag"),
    ("Wolters Kluwer", "Technologie", "SAP ERP-implementatie via SOA People.", "Gemiddeld"),
    ("Universiteit Leiden", "Onderwijs", "Geïntegreerde SAP ERP-oplossing (inkoop, verkoop, facturatie, HR self-service).", "Gemiddeld"),
    ("Erasmus Universiteit Rotterdam", "Onderwijs", "Bestaande SAP-klant, moderniseert richting S/4HANA voor HR/Finance.", "Gemiddeld"),
    ("Tilburg University", "Onderwijs", "SAP SuccessFactors (gemigreerd vanaf SAP HCM); actieve SAP-beheerdersvacatures.", "Gemiddeld"),
    ("Basiq Dental", "Groothandel", "SAP S/4HANA Cloud + SAP Datasphere, via Ctac.", "Gemiddeld"),
]

EINDKLANTEN_UITGEBREID_NOTE = (
    "Deze 60 bedrijven zijn een aanvulling op de kernlijst (1a), individueel gebronnen via SAP-eigen "
    "klantverhalen, cases van implementatiepartners (Ctac, Capgemini, Accenture, Deloitte, Quinso, "
    "myBrand, NTT DATA, PwC, BearingPoint e.a.), Nederlandse vakpers (Computable, AG Connect, Zorgvisie, "
    "Skipr) en vacatureteksten. Ook hier geldt: 'Laag' betekent alleen een aggregator- of indirecte bron, "
    "geen bevestiging uit eerste hand."
)

BULK_APPENDIX_INTRO = (
    "De bovenstaande 77 bedrijven (17 kernlijst + 60 uitgebreid) zijn een individueel gebronde selectie — "
    "geen volledige telling. Dataleverancier TheirStack (technologie-detectie op basis van vacatures, "
    "scripts en metadata) claimt aanzienlijk grotere aantallen SAP-gebruikers in Nederland. Onderstaande "
    "cijfers en namen zijn <b>niet individueel geverifieerd</b> — puur bedoeld als aanvullende leads."
)

BULK_APPENDIX_COUNTS = [
    ("SAP (alle producten)", "~2.103-2.245 bedrijven"),
    ("SAP S/4HANA (SAP Cloud ERP)", "~283-293 bedrijven"),
    ("SAP ECC R/3", "158 bedrijven"),
    ("SAP Ariba", "143-145 bedrijven"),
    ("SAP SuccessFactors", "110-191 bedrijven"),
    ("SAP HCM", "57-71 bedrijven"),
    ("SAP Concur", "32 bedrijven"),
    ("SAP Controlling", "11-15 bedrijven"),
    ("SAP Business ByDesign", "5-8 bedrijven"),
    ("SAP Quality Management", "4-5 bedrijven"),
]

BULK_APPENDIX_NAMES = (
    "Namen zichtbaar in de publieke voorbeeldrijen van TheirStack (bron: theirstack.com/en/technology/sap/nl "
    "e.a., juli 2026 — volledige lijst achter betaalmuur): Philips, AkzoNobel, ASML, The HEINEKEN Company, "
    "FrieslandCampina, Ministerie van Defensie, Nouryon, Signify, Louis Dreyfus Company, Stellantis, TenneT, "
    "BearingPoint, Corbion, Booking.com, Adevinta, ASM International, Finalise, IKEA, Coty, Flora Food Group, "
    "Action, Gasunie, Tilburg University, International Criminal Court, ASICS EMEA, De Klok Dranken, Ahold "
    "Delhaize, Wolters Kluwer, HE Space Operations, Sana Commerce, Plato Group, Aviko, Codestone, Baggr, TMF "
    "Group, JDE Peet's, DLL, Jungheinrich (NL), QIAGEN, LINKIT, GeekSoft Consulting, Daikin Nederland, Enexis, "
    "HMH, Perfact Group, Uzin Utz Nederland BV, Belastingdienst, Belmont Lavan, Aiden, SNV, ISISPACE Group, "
    "Merus N.V., Ormer ICT, AGION, Asecom, Refresco, RedBlue IT Professionals. Namen die ook in de "
    "geverifieerde lijsten hierboven voorkomen (Action, Gasunie, JDE Peet's, TMF Group, Wolters Kluwer, "
    "Tilburg University, Enexis, Belastingdienst) bevestigen dat de aggregator-data reëel signaal bevat; de "
    "rest is <b>niet</b> onafhankelijk gecontroleerd."
)

BULK_APPENDIX_GAPS = (
    "Bekende hiaten in dit onderzoek: pure logistiek/expediteurs (DHL, Kuehne+Nagel, DB Schenker) leverden "
    "geen NL-specifieke SAP-bevestiging op; VodafoneZiggo bleek juist op <b>Oracle</b> te draaien, niet SAP; "
    "een tweede grote bank naast ABN AMRO (bv. ING) kon niet worden bevestigd. Aviko (dochter van Cosun) is "
    "bewust uitgesloten: gebruikt alleen SAP Signavio voor procesmodellering, de kern-ERP is Microsoft "
    "Dynamics."
)

SI_GLOBAAL = [
    ("Accenture", "Platinum", "Wereldwijde SAP-praktijk (15.000+); NL-specifieke SAP-omvang niet gevonden."),
    ("Capgemini", "Platinum", "Wereldwijd 360.000+ medewerkers; historisch sterk in NL; NL-specifieke SAP-omvang niet gevonden."),
    ("Deloitte", "Platinum", "Eigen SAP-dienstenpagina voor NL; omvang niet gevonden."),
    ("EY", "Platinum (impliciet)", "NL-specifieke SAP-transformatiecontent aanwezig."),
    ("PwC", "Platinum", "Actief in SAP SuccessFactors HR-transformatiepraktijk."),
    ("KPMG", "Platinum, RISE with SAP Validated Partner", "Amstelveen HQ; 5.000+ medewerkers wereldwijd; focus finance transformation, risk/compliance, S/4HANA Public/Private Cloud, SuccessFactors."),
    ("Atos / Eviden", "Platinum", "Actief in NL (o.a. Schiphol SuccessFactors-project); wortels in fusie met Nederlandse Origin B.V. (2000)."),
    ("NTT DATA Business Solutions", "Platinum-niveau", "NL-kantoor in 's-Hertogenbosch; 18.500+ experts, 90+ nationaliteiten, 30+ landen; focus food & agri, life sciences, professional services, hoger onderwijs."),
    ("Wipro / Rizing", "Platinum", "Wereldwijd Platinum bevestigd; NL-kantoor niet specifiek gevonden."),
    ("Cognizant", "Platinum", "Bevestigd actief in NL — implementatiepartner bij Rabobank S/4HANA Central Finance / OneFinance."),
    ("TCS", "Platinum", "Wereldwijd Platinum bevestigd; NL-aanwezigheid niet apart geverifieerd."),
    ("Infosys", "Platinum", "Wereldwijd Platinum bevestigd; NL-aanwezigheid niet apart geverifieerd."),
    ("BearingPoint", "Gold", "Amsterdam; 'SAP Partner of the Year 2024' voor Process & Life Sciences; dekt S/4HANA (Public/Private/On-Prem), Ariba, SuccessFactors, BTP."),
]

SI_BOUTIQUE = [
    ("Ctac", "Ja, geverifieerd", "Den Bosch; SAP Gold partner, 51-500 medewerkers; SAP Business One, Business ByDesign, S/4HANA, SuccessFactors, retail/vastgoed-oplossingen."),
    ("Eraneos (voorheen Quint)", "Ja, geverifieerd", "Europese consultancy in 9 landen; NL-vestiging 250+ medewerkers, 30+ jaar actief; SAP is één van meerdere dienstenlijnen."),
    ("Cegeka", "Ja, geverifieerd", "Belgisch familiebedrijf; ca. 1.200 medewerkers in NL na overname KPN Consulting ('Benelux-krachtpatser'); SAP is onderdeel van breder portfolio."),
    ("Devoteam", "Ja, geverifieerd (reële SAP-diepgang onduidelijk)", "Kantoor in Amsterdam; positioneert zich rond AI-gedreven tech consulting, cloud/cyber/data; SAP-specialisme niet duidelijk als kernactiviteit bevestigd."),
    ("Qualiture", "Ja, geverifieerd, NL-based", "SAP-specifieke boutique: SAPUI5, SAP BTP, SAP NetWeaver technisch/functioneel consulting."),
    ("McCoy & Partners", "Ja, gevonden tijdens onderzoek", "Noemt zichzelf 'de SAP-dienstverlener van Nederland'; leverancier bij Schiphol SuccessFactors-project."),
    ("Quinso", "Ja, gevonden via SAP Partner Finder", "Verschijnt direct in SAP's eigen NL-partnerzoekresultaten."),
    ("CNT Management Consulting", "Ja, geverifieerd", "Heeft eigen NL- en België-pagina's voor SAP-consulting."),
]

SI_ONBEVESTIGD = (
    "Niet te verifiëren als actieve, reële NL SAP-consultancy via algemeen websearch: Inspirit, Cormatrix, "
    "Panton, Xite, Approyo, Circle IT, ArjadeQBIT/Qbit, Reply, Prodware, Uniserv, Approach, Yonder — dit "
    "betekent niet per se dat ze niet bestaan, maar er is onvoldoende publiek bewijs om ze hier als "
    "SAP-speler op te nemen. <b>Onestein</b> is een reëel bedrijf, maar specialiseert zich in <b>Odoo</b> "
    "voor het MKB, niet in SAP — ten onrechte in de oorspronkelijke kandidatenlijst opgenomen. "
    "<b>All for One Group</b> is een grote, reële Platinum-partner, maar primair Duits/Oostenrijks/Zwitsers/"
    "Pools gericht; een substantiële zelfstandige NL-tak kon niet worden bevestigd. Voor een volledige, "
    "actuele lijst is de officiële SAP Partner Finder (partnerfinder.sap.com, filter Nederland) de "
    "autoritatieve bron — die noemt volgens een externe aggregator (ERP Research) 351 geverifieerde "
    "NL-partners."
)

ISV_LIJST = [
    ("TrueCommerce", "Ja, actief", "Biedt GROW with SAP-gecertificeerde EDI-integratie voor S/4HANA, plus SAP Business One en ECC/R3 EDI-integraties. Wereldwijd bedrijf, actief in NL-markt."),
    ("Eyefreight", "Bestond, nu opgegaan in Elemica", "Was zelfstandige TMS-leverancier (Transportation Management); nu onderdeel van Elemica's eTMS-suite, geen zelfstandig SAP-add-on merk meer."),
    ("Reybex / Zetadocs / iptor / Zetes", "Niet te verifiëren als NL SAP-ISV", "Geen substantieel bewijs gevonden van NL-specifieke SAP-add-on activiteit."),
]

PARTNERTIERS = [
    "SAP PartnerEdge kent vier engagementmodellen (Build, Sell, Service, Run) en vier niveaus: "
    "<b>Platinum</b> (grote wereldwijde SI's zoals Accenture, Deloitte, IBM, PwC, EY, Capgemini, TCS, "
    "Infosys, Wipro, KPMG, Atos/Eviden, NTT DATA), <b>Gold</b> (grote regionale/gespecialiseerde spelers "
    "zoals BearingPoint, Ctac), <b>Silver</b> (kleinere gecertificeerde partners en ISV's), en "
    "<b>Registered</b> (instapniveau).",
    "SAP's eigen Partner Finder voor Nederland is de autoritatieve, actuele bron "
    "(partnerfinder.sap.com, filter Nederland). Een externe aggregator (ERP Research) claimt "
    "<b>351 geverifieerde SAP-partners</b> en 'meer dan 2.500 SAP-implementaties' in Nederland.",
    "Er is <b>geen gepubliceerd marktaandeel per partner</b> gevonden voor Nederland of Benelux. "
    "Gartner heeft relevante (betaalde, wereldwijde) rapporten, maar niets NL-specifiek publiek "
    "beschikbaar.",
    "<b>ISG kondigde in november 2025</b> een speciale 'ISG Provider Lens: SAP Ecosystem'-studie aan die "
    "onder andere Benelux zal behandelen — resultaten worden rond <b>mei 2026</b> verwacht. Dit wordt de "
    "eerst beschikbare min-of-meer autoritatieve marktaandeel-bron voor de regio; nog niet gepubliceerd "
    "op moment van schrijven.",
    "Marktomvang ter referentie: de totale Benelux ERP-markt (alle leveranciers, niet alleen SAP) wordt "
    "geschat op ca. <b>$1,1 miljard</b> in 2025 (~9% van de Europese ERP-markt); Nederland alleen "
    "ca. <b>$777 miljoen</b>.",
]

FINANCIELE_GEZONDHEID = [
    ("Capgemini", "Kondigde ca. €700 miljoen herstructureringskosten aan over de komende twee jaar "
     "(merendeel in 2026), toegeschreven aan 'veranderende klantvraag en versnelde technologieshift door AI'. "
     "Collectief ontslag in Spanje (11.000 medewerkers geraakt) en mogelijk tot 2.400 banen in Frankrijk. "
     "Tegelijk: FY2025-resultaten overtroffen de omzetgroeidoelstelling, 2026-guidance +6,5% tot +8,5% "
     "omzetgroei. Geen NL-specifieke ontslagcijfers gevonden."),
    ("Air France-KLM", "Publiceerde FY2025-resultaten (19 feb 2026); cijfers beschikbaar maar niet diepgaand "
     "geanalyseerd in dit onderzoek."),
    ("Overige (Deloitte, PwC, EY, KPMG, Accenture, NTT DATA, Wipro, TCS, Infosys, Rabobank, Ahold Delhaize)",
     "Geen NL-specifieke signalen over financiële gezondheid (ontslagen, winstwaarschuwingen, "
     "groeiverrassingen) gevonden in dit onderzoek — dit is een hiaat, geen 'schone lei'. Vervolgonderzoek "
     "(bv. FD.nl, Consultancy.nl archieven) nodig voor een volledig beeld."),
]

FIN_NOTE = (
    "Bredere trend om in de gaten te houden: Capgemini's herstructurering wordt expliciet gekoppeld aan "
    "AI die de vraag naar traditionele delivery-consultants vermindert — een trend die waarschijnlijk ook "
    "SAP-praktijken in bredere zin raakt (meer automatisering bij migratie/testen kan de vraag naar junior "
    "consultants drukken)."
)

WERVING_TEKST = [
    "<b>Grote SI's</b> (Accenture, Capgemini, Deloitte, EY, PwC, KPMG, Atos/Eviden, NTT DATA, Wipro, "
    "Cognizant, TCS, Infosys): overwegend <b>vast/payroll</b>-personeel op schaal, aangevuld met "
    "freelancers voor piekcapaciteit of nichekennis. Grote graduate/analyst-instroomprogramma's.",
    "<b>Middelgrote/boutique NL-consultancies</b> (Ctac, Eraneos, Qualiture, BearingPoint, Cegeka e.d.): "
    "mix van vast personeel en flexibele/interim-inzet, gebruikelijk in de Nederlandse markt.",
    "<b>Freelance/ZZP-markt</b>: zeer groot en actief in de Nederlandse SAP-wereld. Meerdere platforms "
    "richten zich specifiek op SAP interim/ZZP-opdrachten (freelance.nl, freep.nl, Bureau Ad Interim, "
    "zzptarief.nl) — het bestaan van zoveel gespecialiseerde intermediairs is zelf een signaal dat "
    "freelance/ZZP-inzet een structureel belangrijk kanaal is, geen nichegeval.",
]

TARIEVEN = [
    ("Freelance/ZZP SAP-consultant (gemiddeld, excl. btw)", "~ €102/uur (sommige bronnen tot ~€115/uur piek)"),
    ("Freelance/ZZP medior consultant", "~ €90-110/uur excl. btw"),
    ("Freelance/ZZP senior/niche (BTP, S/4HANA-architectuur, programmalead)", "indicatief €120-150+/uur — niet hard onderbouwd, alleen anekdotisch"),
    ("Vast salaris SAP-consultant (NL, algemeen)", "~ €4.000-8.000/maand afhankelijk van niveau"),
    ("Vast salaris, instap - top (jaarbasis, Payscale)", "€27.480 - €87.040/jaar"),
    ("Vast salaris, Amsterdam (Glassdoor, 25e-75e percentiel)", "€51.075 - €79.445/jaar, topdeciel tot ~€103.400/jaar"),
]

TARIEVEN_NOTE = (
    "Michael Page NL (Salary Guide 2026), Robert Walters NL (Salary Survey 2026) en Harvey Nash "
    "(Tech Talent & Salary Report 2026) zijn relevante, actuele bronnen, maar SAP-specifieke "
    "regels konden dit onderzoek niet uit de (afgeschermde/lange) documenten halen — aanrader om "
    "deze direct te raadplegen voor een verdiepingsslag."
)

CONSULTANT_ROLLEN = [
    ("Integratieconsultant", "Ontwerpt/bouwt koppelingen tussen S/4HANA en andere SAP/non-SAP-systemen via "
     "SAP BTP, Cloud Integration (CI/CPI), API Management en Advanced Event Mesh. Actief geadverteerde, "
     "gevraagde categorie op NL-vacaturesites."),
    ("Basis/technisch consultant", "Beheert systeembeheer, installatie, upgrades, performance-tuning, "
     "beveiliging en infrastructuur (on-prem, cloud of hybride); cruciaal bij elke S/4HANA-migratie."),
    ("Functioneel consultant (FI/CO, MM, SD, PP, ...)", "Configureert en adviseert over specifieke "
     "bedrijfsprocessen — Finance & Controlling, Materials Management, Sales & Distribution, Production "
     "Planning, HCM/SuccessFactors, EWM, QM. Blijft de grootste vraagcategorie, sectoroverstijgend."),
    ("ABAP-ontwikkelaar", "Bouwt maatwerkcode, rapportages, interfaces en extensies; steeds vaker richting "
     "'clean core'-ontwikkeling op BTP (side-by-side extensies) in plaats van in-core aanpassingen, "
     "conform SAP's eigen S/4HANA- en RISE-richting."),
    ("BTP/CPI-specialist", "Nieuwere, snelgroeiende categorie — cloud-native integratie en "
     "extensieontwikkeling op het platformniveau van SAP; expliciet genoemd als apart, actief gevraagd "
     "specialisme in NL-vacatures."),
]

ROLLEN_NOTE = (
    "Vraagsignalen (voorjaar 2026, Indeed NL/Glassdoor NL): substantieel en groeiend aantal vacatures voor "
    "SAP BTP (~75+ gelijktijdige vacatures), SAP CPI (~25+), en algemeen SAP-consultant (~200+) — consistent "
    "met het beeld dat BTP/cloud-integratie en S/4HANA-migratiekennis momenteel de meest gevraagde "
    "sub-specialismen zijn, bovenop een stabiele basisvraag naar functionele consultants. Er is geen "
    "harde, officiële 'moeilijkst te vervullen rol'-ranking specifiek voor NL gevonden — bovenstaand beeld "
    "is afgeleid van relatief vacaturevolume, geen formele schaarste-index."
)

PRODUCTLANDSCHAP = [
    ("S/4HANA (on-premise)", "SAP's moderne ERP-suite op de in-memory HANA-database, opvolger van ECC/"
     "Business Suite. On-premise wordt geïnstalleerd en beheerd in eigen of gehost datacenter — maximale "
     "controle/maatwerk, maar de klant (of SI) beheert upgrades en infrastructuur zelf."),
    ("S/4HANA Cloud, Private Edition", "Single-tenant cloudversie van dezelfde (on-prem-vergelijkbare) "
     "codebasis, doorgaans geleverd via RISE with SAP; net zo diep aan te passen als on-prem, maar met "
     "door SAP/hyperscaler beheerde infrastructuur."),
    ("S/4HANA Cloud, Public Edition", "Multi-tenant SaaS-ERP met gestandaardiseerde best-practice-processen, "
     "sneller/goedkoper te implementeren (SAP noemt 8-12 weken via GROW with SAP), minder aan te passen, "
     "continue kwartaalupdates, 'clean core'-filosofie (maatwerk naar BTP-extensies)."),
    ("SAP BTP (Business Technology Platform)", "SAP's platform-as-a-service-laag voor extensies, "
     "integraties en apps rond de ERP-kern — combineert applicatieontwikkeling (ABAP Cloud, Java, "
     "low-code), integratietooling, data- en analyticsdiensten en AI-diensten."),
    ("SAP Integration Suite / CPI (Cloud Platform Integration)", "BTP's beheerde integratiedienst — "
     "kant-en-klare connectors/iFlows om SAP en non-SAP-systemen te koppelen, API-beheer, "
     "event-gedreven integratie en B2B/EDI-beheer."),
    ("SAP IAS (Identity Authentication Service)", "Cloud-identiteitsprovider voor authenticatie (SSO, MFA) "
     "over SAP cloud- en on-prem-applicaties — de 'voordeur' voor gebruikersinlog."),
    ("SAP IPS (Identity Provisioning Service)", "Automatiseert aanmaken/bijwerken/intrekken van "
     "gebruikersaccounts over gekoppelde SAP- en non-SAP-systemen, meestal samen met IAS."),
    ("SAP Ariba", "Cloudgebaseerd inkoop- en leveranciersplatform (sourcing, contracten, supplier network, "
     "spend management)."),
    ("SAP SuccessFactors", "Cloud HCM-suite — Employee Central (kern-HR), payroll, recruiting, learning, "
     "performance & goals, opvolgplanning. Vaak als eerste gemigreerd, ook door bedrijven die nog op ECC "
     "draaien (zie Schiphol, PostNL)."),
    ("SAP Concur", "Cloud reis- en onkostenbeheer (T&E) — onkostendeclaraties, reisboekingen, "
     "factuurbeheer."),
    ("SAP Analytics Cloud (SAC)", "Cloud BI/planning/predictive analytics — rapportage, dashboards en "
     "financiële planning in één product."),
    ("SAP Datasphere / BW/4HANA", "Datasphere is SAP's nieuwere cloud-datalaag (federatie, cataloging, "
     "semantisch modelleren over SAP en non-SAP-bronnen); BW/4HANA blijft het on-prem/private-cloud "
     "datawarehouse-product voor bestaande klanten. Datasphere staat centraal in de 'Business Data Cloud'"
     "-strategie van 2026."),
    ("SAP Build", "Low-code/no-code-suite op BTP — Build Apps, Build Process Automation en Build Work Zone "
     "— gericht op citizen developers en snellere extensie-ontwikkeling rond de 'clean core'."),
]

NIEUWE_ONTWIKKELINGEN = [
    "<b>SAP Green Ledger</b> — algemeen beschikbaar sinds januari 2025; koolstofboekhouding geïntegreerd in "
    "financiële processen, draait op SAP BTP, geïntegreerd met S/4HANA Cloud finance; onderdeel van RISE "
    "en GROW with SAP. Q1 2026: uitgebreid met koolstofcertificaten en -verplichtingen, deels gedreven door "
    "de EU CBAM (Carbon Border Adjustment Mechanism) die per januari 2026 ingaat.",
    "<b>Einde onderhoud ECC/Business Suite 7</b>: mainstream onderhoud voor ECC 6.0 zonder/met EHP1-5 "
    "eindigde 31 dec 2025; met EHP6-8 eindigt het 31 dec 2027. Extended maintenance loopt tot 31 dec 2030 "
    "(~9% meerkosten). Sinds Q1 2025: 'SAP ERP, private edition, transition option' — kan support tot 2033 "
    "verlengen, maar alleen gekoppeld aan een RISE-contract, geen algemene verlenging.",
    "<b>SAP Sapphire 2026 (mei 2026)</b> — thema 'Autonomous Enterprise': CEO Christian Klein introduceerde "
    "50+ Joule digitale assistenten, 200+ gespecialiseerde AI-agents, een partnerfonds van €100 miljoen, en "
    "agent-gestuurde migratietools die migratie-inspanning met 35%+ zouden verminderen.",
    "SAP consolideert <b>BTP + Business Data Cloud (BDC) + AI Foundation</b> tot één architectuur, met een "
    "'SAP Knowledge Graph' die decennia aan ERP-proces-/datasemantiek vastlegt.",
    "<b>'Joule Work'</b> — nieuwe natuurlijke-taal-interface die traditionele app-navigatie moet vervangen "
    "door intentiegestuurde, agent-ondersteunde uitvoering.",
    "<b>Business Data Cloud-partnerships</b>: SAP bevestigde/breidde open-data-ecosysteempartnerships uit "
    "met Databricks, Snowflake, Google BigQuery en Microsoft Fabric ('zero-copy' datadeling).",
    "SAP kondigde <b>voorgenomen overname van Dremio</b> aan, gericht op een natieve enterprise Lakehouse "
    "binnen Business Data Cloud.",
    "SAP noemde <b>Anthropic's Claude</b> als primair redeneermodel achter Joule in de 'Autonomous Suite', "
    "vanwege de meerstaps-redeneercapaciteit die nodig is voor betrouwbare enterprise-agentworkflows onder "
    "beveiligings-/compliance-eisen.",
    "De <b>ISG SAP Ecosystem-studie</b> (aangekondigd nov 2025, Benelux-resultaten verwacht ~mei 2026) is "
    "zelf een ontwikkeling om te volgen als eerste min-of-meer autoritatieve marktaandeel-bron voor de "
    "regio.",
]

HIATEN = [
    "Geen autoritatieve marktaandeelpercentages per partner voor NL/Benelux — de ISG Benelux-studie is nog "
    "niet gepubliceerd (verwacht ~mei 2026).",
    "De boutique-consultancylijst is slechts deels verifieerbaar — meerdere in de oorspronkelijke vraag "
    "genoemde namen (Inspirit, Cormatrix, Panton, Xite, Approyo, Circle IT, Qbit, Reply, Prodware, Uniserv, "
    "Approach, Yonder) konden niet worden bevestigd als reële, actieve NL SAP-spelers; Onestein bestaat wel "
    "maar is Odoo-gericht, niet SAP; All for One's zelfstandige NL/Benelux-aanwezigheid is onbevestigd.",
    "De ISV/add-on-laag is dun gedocumenteerd — alleen TrueCommerce is bevestigd als actieve, "
    "SAP-gerelateerde ISV relevant voor NL; Eyefreight is opgegaan in Elemica; Reybex/Zetadocs/iptor/Zetes "
    "konden niet worden bevestigd.",
    "Financiële gezondheid per bedrijf (buiten Capgemini en Air France-KLM) is niet gevonden voor de "
    "meeste genoemde partijen specifiek voor NL — dit is een echt hiaat, geen bevestiging van stabiliteit.",
    "Vopak stond in de oorspronkelijke voorbeeldenlijst als eindklant, maar is géén actieve SAP-klant "
    "(gebruikt Oracle Cloud ERP/Fusion + Workday) — hierboven gecorrigeerd.",
    "ING's SAP-voetafdruk kon niet worden bevestigd — geen bewijs in beide richtingen gevonden.",
]

CONTACTS_NOTE = (
    "Methodologie: onderstaande contactkanalen en functietitels komen uitsluitend van de bedrijven zelf "
    "(contactpagina's, leveranciers-/procurementpagina's, vacaturepagina's) of van publiek gepubliceerde "
    "bronnen (persberichten, partnerpagina's). Er is bewust <b>niet</b> op individuele LinkedIn-profielen "
    "gescraped. Een klein aantal namen wordt genoemd omdat het bedrijf ze zelf publiceert op een "
    "praktijk-/contactpagina (bv. een 'ons team'-pagina) — deze zijn expliciet gemarkeerd met "
    "<i>(naam, verifiëren voor gebruik)</i> omdat rollen snel wisselen en dit niet character-voor-character "
    "is herverifieerd. Waar geen zinvol publiek SAP/IT-procurementcontact bestaat, staat dat vermeld in "
    "plaats van verzonnen."
)

CONTACTS_EINDKLANTEN = [
    ("Shell", "Geen SAP/IT-procurementcontact publiek; <link href='https://www.shell.com/who-we-are/contact-us.html'>algemene contactpagina</link>. Vacatures: <link href='https://www.shell.com/careers.html'>shell.com/careers</link>", "IT Procurement / Vendor Management (generiek, niet bevestigd)"),
    ("Heineken", "Geen dedicated contact; <link href='https://www.linkedin.com/company/heineken'>LinkedIn-bedrijfspagina</link>. Vacatures: <link href='https://careers.theheinekencompany.com/'>careers.theheinekencompany.com</link>", "Digital &amp; Technology (D&amp;T) — IT Procurement/Vendor Management"),
    ("KLM / Air France-KLM", "<link href='https://procurement.airfranceklm.com/procurement/en/pageStandard/homepage.html'>Procurement-portal AFKLM</link>. Vacatures: <link href='https://careers.klm.com/en/campaign/become-a-sap-consultant-at-klm/'>SAP-campagnepagina KLM</link>", "Tech &amp; Data / Information Services"),
    ("Philips", "<link href='https://www.philips.com/a-w/about/suppliers/working-with-philips.html'>Supplier-portal</link>. Vacatures: <link href='https://jobs.philips.com/jobs/?q=sap'>jobs.philips.com (SAP-filter)</link>", "Procurement / Supplier Management"),
    ("ASML", "<link href='https://www.asml.com/en/products/supplier-net'>SupplierNet</link> (bestaande leveranciers) / <link href='https://www.asml.com/en/contacts/contact-us'>contactpagina</link>. Vacatures: <link href='https://www.asml.com/en/careers/find-your-job'>asml.com/careers</link>", "Sourcing &amp; Supply Chain / IT — Support Functions"),
    ("Ahold Delhaize (ADUSA)", "<link href='https://www.adusa.com/interested-suppliers'>Leveranciersportal ADUSA</link>. Vacatures: <link href='https://careers.aholddelhaize.com/vacancies'>careers.aholddelhaize.com</link>", "IT / SAP Data Platform CoE"),
    ("DSM-Firmenich (Twilmij)", "<link href='https://our-company.dsm-firmenich.com/en/our-company/suppliers.html'>Leverancierspagina</link>. Vacatures: <link href='https://jobs.dsm-firmenich.com/careers/it?domain=dsm.com'>jobs.dsm-firmenich.com (IT)</link>", "IT/SAP inkoop of partnerships (generiek)"),
    ("Unilever Benelux", "<link href='https://supplierhelpportal.unilever.com/csm'>Supplier Qualification/Helpdesk</link>. Vacatures: <link href='https://careers.unilever.com/en/netherlands'>careers.unilever.com/netherlands</link>", "Procurement Manager (adresseer generiek)"),
    ("Rabobank", "<link href='https://www.rabobank.com/about-us/suppliers/prisma'>PRISMA supplier onboarding</link>. Vacatures: <link href='https://rabobank.jobs/en/expertise/it/'>rabobank.jobs (IT)</link>", "Procurement / IT — SAP Integration team"),
    ("Schiphol Group", "<link href='https://www.schiphol.nl/nl/schiphol-group/contact-procurement/'>Dedicated procurement-contactpagina</link>. Vacatures: <link href='https://www.werkopschiphol.nl/vakgebieden/it-data/werken-in-de-it-data'>werkopschiphol.nl (IT &amp; Data)</link>", "Procurement (Chief Procurement Officer's office)"),
    ("PostNL", "<link href='https://www.postnl.nl/en/en/about-postnl/governance/procurement/'>Procurement Policy-pagina</link> (geen direct contact). Vacatures: <link href='https://www.postnl.nl/over-postnl/werkenbij/professionals/it/'>postnl.nl/werkenbij (IT)</link>", "IT Procurement / Team Suppliers &amp; Customers"),
    ("AkzoNobel", "<link href='https://www.akzonobel.com/en/about-us/for-suppliers/become-an-akzonobel-supplier-'>'Become a supplier'-formulier</link>. Vacatures: <link href='https://careers.akzonobel.com/'>careers.akzonobel.com</link>", "Purchasing / Procurement (generiek)"),
    ("FrieslandCampina", "procurement.vendormanagement@frieslandcampina.com. Vacatures: <link href='https://careers.frieslandcampina.com/'>careers.frieslandcampina.com</link>", "Procurement — Vendor Management (EMEA)"),
    ("Signify", "<link href='https://www.signify.com/global/contact/suppliers/portal'>Supplier-portal</link>. Vacatures: <link href='https://www.careers.signify.com/global/en/technology'>careers.signify.com (Technology)</link>", "Procurement / Supplier Management"),
    ("Nouryon", "support.vendorportal@nouryon.com. Vacatures: <link href='https://www.nouryon.com/careers/vacancies/'>nouryon.com/careers</link>", "Chief Integrated Supply Chain Officer's organisatie (senior/globaal — niet als direct contact gebruiken)"),
    ("Louis Dreyfus Company", "<link href='https://www.ldc.com/contact-us/'>Algemene contactpagina</link>. Vacatures: <link href='https://www.ldc.com/careers/'>ldc.com/careers</link>", "Procurement — IT &amp; Telecommunications sourcing"),
    ("Ministerie van Defensie", "<link href='https://www.defensie.nl/contact/zakendoen-met-defensie/informatie-voor-leveranciers'>Zakendoen-met-Defensie</link>. Vacatures: <link href='https://werkenbijdefensie.nl/'>werkenbijdefensie.nl</link> (o.a. 'Senior Medewerker SAP')", "Directie Inkoop, COMMIT (~15 fte IT-inkoop, ~€1 mrd/jaar IT-uitgaven)"),
]

CONTACTS_SI_GLOBAAL = [
    ("Accenture", "<link href='https://accenture.com/nl-en/contact-us'>Contact NL</link>. Vacatures: <link href='https://www.accenture.com/nl-en/careers/explore-careers/area-of-interest/sap-careers'>SAP careers NL</link>", "SAP Practice Lead / Ecosystem &amp; SAP Alliances"),
    ("Capgemini", "Algemene NL-carrièrepagina, geen publieke NL-SAP-lead gevonden. Vacatures: <link href='https://www.capgemini.com/nl-nl/ontdek-sap-vacatures-bij-capgemini/'>SAP-vacaturepagina</link>", "SAP Practice / SAP Business Unit NL (generiek)"),
    ("Deloitte", "<link href='https://www.deloitte.com/nl/en/alliances/sap.html'>SAP-alliance-pagina</link> (naam, verifiëren voor gebruik: Joeri Bergacker — SAP Solutions Service Line NL; Monique van Kraay — Ecosystems &amp; Alliances). Vacatures: <link href='https://werkenbijdeloitte.nl/vacatures/13-enterprise-technology-performance/71-sap'>werkenbijdeloitte.nl (SAP-filter)</link>", "SAP Solutions Service Line / Ecosystems &amp; Alliances"),
    ("EY", "<link href='https://www.ey.com/en_nl/alliances/sap'>SAP-alliance-pagina</link>. Vacatures: <link href='https://www.ey.com/en_nl/careers/job-search'>ey.com/en_nl/careers</link>", "EY–SAP Alliance Team"),
    ("PwC", "<link href='https://www.pwc.nl/en/services/technology-alliances/sap.html'>SAP-alliance-pagina</link>. Vacatures: <link href='https://www.pwc.nl/en/careers/business-areas/technologyconsulting/join-our-sap-team-and-work-with-the-best.html'>Technology Consulting — SAP</link>", "Technology Consulting — SAP team"),
    ("KPMG", "<link href='https://kpmg.com/nl/en/contact.html'>Contactpagina</link> (naam, verifiëren voor gebruik: Keesjan van Unen — Data Management/ERP-strategie; eventcontact Guido ter Riet voor SAP-events). Vacatures: <link href='https://www.werkenbijkpmg.nl/en/vacancies?interest=it_platforms'>werkenbijkpmg.nl (IT-platforms)</link>", "SAP S/4HANA Services / Powered Enterprise SAP"),
    ("Atos / Eviden", "Geen NL-specifieke SAP-praktijkcontact gevonden; <link href='https://sapeducation.atos.net/contact-us/'>SAP-education-contact</link>. Vacatures: <link href='https://eviden.com/careers/'>eviden.com/careers</link>", "SAP Practice (generiek)"),
    ("NTT DATA Business Solutions", "<link href='https://nttdata-solutions.com/bnl/contact/'>Benelux-contact</link> ('s-Hertogenbosch). Vacatures: <link href='https://careers.nttdata-solutions.com/?locale=nl_NL'>careers.nttdata-solutions.com</link>", "Sales NL-team (goede proxy voor partnership-vragen)"),
    ("Wipro / Rizing", "<link href='https://www.wipro.com/en-benelux/overview/'>Wipro Benelux-overzicht</link> / <link href='https://rizing.com'>rizing.com</link>. Vacatures: <link href='https://careers.wipro.com/global-europe-benelux/jobs'>careers.wipro.com</link> (let op fraude-waarschuwing, alleen officiële kanalen)", "SAP Practice (generiek)"),
    ("Cognizant", "<link href='https://careers.cognizant.com/emea-en/our-locations/netherlands/'>NL-locatiepagina</link>. Vacatures: zelfde link — noemt Rabobank, ING, ABN AMRO, Ikea, Booking.com als NL-klanten sinds 2006", "SAP/ERP Services — Benelux"),
    ("TCS", "<link href='https://info.tcs.com/SAP-practice-contact-us..html'>SAP-praktijk contactformulier</link> (globaal, routeert regionaal). Vacatures: <link href='https://www.tcs.com/careers/netherlands'>tcs.com/careers/netherlands</link>", "SAP Practice (21.200 consultants wereldwijd; NL-klanten o.a. KLM, Philips, ABN AMRO, Rabobank volgens TCS zelf)"),
    ("Infosys", "Geen NL-specifiek contact; <link href='https://www.infosys.com/about/alliances/sap.html'>SAP-alliance-pagina</link> (Tarang Puranik, EVP — senior/globaal). Vacatures: <link href='https://digitalcareers.infosys.com/infosys/global-careers?location=Netherlands'>digitalcareers.infosys.com (NL-filter)</link>", "SAP Digital Platforms Practice — Europe"),
    ("BearingPoint", "<link href='https://www.bearingpoint.com/en-nl/services/technology-partners/sap/'>SAP-praktijkpagina</link>. Vacatures: <link href='https://bearingpointnl.recruitee.com/'>bearingpointnl.recruitee.com</link>", "SAP Practice (Gold Partner, 2.100+ SAP-consultants wereldwijd)"),
]

CONTACTS_SI_BOUTIQUE = [
    ("Ctac", "<link href='https://www.ctac.nl/CONTACT'>Contactpagina</link> / <link href='https://www.ctac.nl/sap-consultancy'>SAP-consultancypagina</link>. Vacatures: <link href='https://www.werkenbijctac.nl/SAP-league'>werkenbijctac.nl (SAP-league)</link>", "SAP Consultancy / Resourcing (bemiddelt ook zelf SAP-freelancers)"),
    ("Eraneos", "info.nl@eraneos.com, +31 20 305 3700. Vacatures: <link href='https://careers.eraneos.com/nl/en/vacancies/'>careers.eraneos.com/nl</link>", "Technology &amp; Platforms — SAP"),
    ("Cegeka", "info@cegeka.nl, kantoren Veenendaal (+31 318 41 00 00) &amp; Eindhoven. Vacatures: <link href='https://www.cegeka.com/nl-nl/werkenbij/vacatures'>cegeka.com/nl-nl/werkenbij</link>", "Professional Services — On-premise ERP/SAP (dedicated account manager per klant)"),
    ("Devoteam", "nl.recruitment@devoteam.com (recruitment). Vacatures: <link href='https://nl.devoteam.com/nl/werken-bij/'>nl.devoteam.com/werken-bij</link>", "SAP Business Unit / SAP Managed Services"),
    ("Qualiture", "Website niet goed te doorzoeken dit onderzoek — hiaat; <link href='https://www.linkedin.com/company/qualiture'>LinkedIn-bedrijfspagina</link> als terugval. Vacatures: onbevestigd, aanrader: qualiture.nl direct bezoeken", "SAP BTP/UI5 Consultancy (generiek)"),
    ("McCoy &amp; Partners", "<link href='https://mccoy-partners.com/en'>mccoy-partners.com</link> (Eindhoven HQ; ook Utrecht/Manila/Madrid) — namen (naam, verifiëren voor gebruik: Marieke Pullen, Jan Laros, Eric Bigot, Thomas van de Wouw) niet live herverifieerd. Vacatures: <link href='https://www.werkenbijmccoy.nl/'>werkenbijmccoy.nl</link>", "SAP Consultancy / Resourcing (grootste onafhankelijke SAP-implementatiepartner van NL, 300+ medewerkers)"),
    ("Quinso", "info@quinso.com, +31 (0)73 206 22 00 (naam, verifiëren voor gebruik: Hubert Wezenberg, Managing Partner). Vacatures: <link href='https://www.quinso.com/en/working-at/'>quinso.com/working-at</link>", "SAP Consultancy (onderdeel ORBIS-familie; focus industrie/groothandel, SAP IBP, RISE with SAP)"),
    ("CNT Management Consulting", "<link href='https://www.cnt-online.com/sap-consulting-nl/'>NL SAP-consultingpagina</link> (details niet volledig op te halen). Vacatures: <link href='https://jobs.cnt-online.com/'>jobs.cnt-online.com</link>", "SAP Consulting (Wenen HQ, 500+ consultants, 25 jaar SAP S/4HANA-focus)"),
]

CONTACTS_ISV = [
    ("TrueCommerce", "<link href='https://www.truecommerce.com/contact/support/'>Support-contact</link> / <link href='https://www.truecommerce.com/partner-program/'>partnerprogramma</link>. Vacatures: <link href='https://www.truecommerce.com/careers/'>truecommerce.com/careers</link> (geen NL-specifieke vacatures)", "Partner Program (reseller/referral/co-marketing)"),
    ("Eyefreight (nu onderdeel Elemica)", "Bunnik/Utrecht HQ voor Eyefreight; geen apart NL-nummer gevonden, algemeen Elemica-contact. Vacatures: <link href='https://eyefreight.com/about-us/careers/'>eyefreight.com/careers</link> / <link href='https://elemica.com/about/careers'>elemica.com/careers</link>", "Partnerships"),
]

RECRUITMENT_BUREAUS = [
    ("Eursap", "Boutique SAP-only, vast + freelance/interim, 21 Europese landen", "Noemt zelf AkzoNobel, Heineken, Nike als klanten; claimt 9.000+ NL-geregistreerde SAP-consultants — <link href='https://eursap.eu/sap-recruitment/netherlands'>eursap.eu</link>"),
    ("Michael Page NL", "Algemeen IT-recruiter met SAP-vertical, vast + freelance", "Geen specifieke naamklant gevonden — <link href='https://www.michaelpage.nl/en/jobs/sap/netherlands'>michaelpage.nl</link>"),
    ("Robert Walters NL", "Algemene professional recruitment, SAP incidenteel", "Geen NL-SAP-specifiek klantbewijs gevonden — <link href='https://www.robertwalters.nl/vacatures.html'>robertwalters.nl</link>"),
    ("Harvey Nash NL", "Vast + interim/freelance contractplaatsing", "Opdrachten gevonden bij Enexis en DUO — <link href='https://www.harveynash.nl/'>harveynash.nl</link>"),
    ("Hays NL", "Algemeen IT, duidelijk SAP-functieprofiel (functioneel vs. technisch)", "Geen NL-klantcasus gevonden — <link href='https://www.hays.nl/sap-consultant-vacature'>hays.nl</link>"),
    ("Yacht (Randstad Professional)", "Detachering; onderscheidt technisch/functioneel SAP (FICO, SCM, CRM, Dev, BI/Data, Cloud)", "Noemt Rijksoverheid als klantverticaal — <link href='https://www.yacht.nl/onze-opdrachtgevers/rijksoverheid'>yacht.nl</link>"),
    ("Between / Striive", "Pure ZZP/freelance-marktplaats ('opdrachten'), geen vaste plaatsing", "Platformniveau, geen specifieke klant toegewezen — <link href='https://striive.com/nl/zzp/opdrachten/sap'>striive.com</link>"),
    ("USG People / Unique (RGF Staffing NL)", "Algemene staffing/payroll/detachering, geen bevestigde SAP-vertical", "Geen SAP-specifiek klantbewijs gevonden — <link href='https://www.usgprofessionals.nl/'>usgprofessionals.nl</link>"),
    ("freelance.nl", "ZZP/freelance-marktplaats (250.000+ freelancers), SAP-categorie functioneel gesplitst", "Platformniveau — <link href='https://www.freelance.nl/sap-consultant'>freelance.nl/sap-consultant</link>"),
    ("freep.nl", "ZZP/interim-opdrachtenplatform", "Opdrachten bij NS en Stedin Groep (SAP FICO/SD, EPPM, Basis, autorisatie) — let op: sommige opdrachten niet DBA-compliant voor directe ZZP-inhuur — <link href='https://www.freep.nl/opdracht/sap-consultant-1'>freep.nl</link>"),
    ("Bureau Ad Interim", "Interim/freelance/ZZP-bemiddelaar, 'no match no pay'", "Geen specifieke naamklant gevonden — <link href='https://bureauadinterim.nl/sap-consultant-freelance-interim-zzp'>bureauadinterim.nl</link>"),
    ("YER", "Vast + gestructureerde SAP-traineeships", "Geen eenduidige naamklant bevestigd — <link href='https://www.yer.nl/vacatures/v-20039767-sap-consultant-maintenance/'>yer.nl</link>"),
    ("Undutchables", "Internationale/expat-recruitment, SAP geen dedicated vertical", "Geen SAP-specifiek klantbewijs gevonden — <link href='https://undutchables.nl/vacancies'>undutchables.nl</link>"),
    ("Global Enterprise Partners (SThree)", "Dedicated enterprise-tech freelance/contractplaatsing voor SAP, Oracle, Microsoft Dynamics, Salesforce; HQ Amsterdam", "Positioneert zich als SAP-specialist binnen SThree (relevanter dan zusterbrand Computer Futures) — <link href='https://www.globalenterprisepartners.com/en-nl/'>globalenterprisepartners.com</link>"),
    ("ICT Group", "Detachering/consultancy industriële IT; SAP is één van vele skill-categorieën", "Geen SAP-specifiek klantbewijs gevonden — <link href='https://jobs.ict.eu/en/vacancies'>jobs.ict.eu</link>"),
]

RECRUITMENT_NOTE = (
    "Niet te verifiëren als actief/SAP-relevant in NL: <b>Piening</b> (wel een Nederlands/Duits "
    "industrieel uitzendbureau bekend, maar geen SAP-specialisatie gevonden) en <b>Passionate Bulldog</b> "
    "(geen zoekresultaten die een bureau met deze naam in de NL SAP-markt bevestigen — mogelijk onjuiste "
    "naam, zeer kleine/niet-geïndexeerde boutique, of niet meer actief)."
)

DISCLAIMER = (
    "Dit rapport is samengesteld op basis van publiek beschikbare webbronnen (bedrijfswebsites, "
    "vacatureteksten, SAP-eigen nieuwsberichten, brancheanalyses en aggregators zoals TheirStack en "
    "ERP Research) en is bedoeld als startpunt voor verdere verkenning, niet als volledige of "
    "gegarandeerd actuele marktanalyse. Marktaandeel, exacte productscope per bedrijf en financiële "
    "gezondheid zijn zelden volledig publiek verifieerbaar — waar dat gold, is dat expliciet vermeld "
    "in plaats van verzonnen. Controleer belangrijke aannames (bv. vacatures, tarieven, contactpartners) "
    "altijd zelf voordat u erop handelt."
)


def make_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("TitleFriendly", parent=styles["Title"], textColor=NAVY),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=styles["Normal"], textColor=GREY,
            alignment=TA_CENTER, fontSize=10, spaceAfter=16,
        ),
        "h2": ParagraphStyle(
            "H2", parent=styles["Heading2"], textColor=NAVY, spaceBefore=16, spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "H3", parent=styles["Heading3"], textColor=BLUE, spaceBefore=10, spaceAfter=6,
        ),
        "body": ParagraphStyle("BodyFriendly", parent=styles["BodyText"], leading=14, spaceAfter=6),
        "note": ParagraphStyle(
            "Note", parent=styles["BodyText"], leading=13, spaceAfter=8,
            textColor=colors.HexColor("#555555"), fontSize=9,
        ),
        "small": ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=GREY),
        "cell": ParagraphStyle("Cell", parent=styles["BodyText"], fontSize=8, leading=10),
    }


def make_table(header, rows, col_widths, styles, conf_col=None):
    data = [header] + rows
    tbl_data = []
    for row in data:
        tbl_data.append([Paragraph(str(c), styles["cell"]) for c in row])

    tbl = Table(tbl_data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_ROW]),
    ]
    tbl.setStyle(TableStyle(cmds))
    return tbl


def build_pdf():
    styles = make_styles()
    doc = SimpleDocTemplate(
        str(PDF_OUTPUT_PATH), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        title="SAP Marktverkenning Nederland", author=REPORT_AUTHOR, subject="SAP NL Marktrapport",
    )
    story = []

    story.append(Paragraph("SAP Marktverkenning Nederland", styles["title"]))
    story.append(Paragraph(
        f"Opgesteld door {REPORT_AUTHOR} &middot; Gegenereerd op "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')} &middot; Onderzoeksrapport, geen garantie voor "
        f"volledigheid",
        styles["subtitle"],
    ))

    story.append(Paragraph(
        "Dit rapport brengt de SAP-markt in Nederland in kaart: eindklanten, consultancy- en "
        "implementatiepartners, softwarebouwers, SAP-partnertiers en marktaandeel-signalen, financiële "
        "gezondheid, wervingsmodellen en tarieven, consultantrollen, een referentie van het "
        "SAP-productlandschap, en recente SAP-ontwikkelingen. Betrouwbaarheid is overal expliciet gemaakt "
        "(Hoog/Gemiddeld/Laag) — waar iets niet publiek verifieerbaar was, is dat als hiaat benoemd in "
        "plaats van ingevuld met een gok.",
        styles["body"],
    ))
    story.append(Spacer(1, 6))

    # 1. Eindklanten
    story.append(Paragraph("1. Eindklanten in Nederland", styles["h2"]))
    story.append(Paragraph("1a. Kernlijst — grootste/bekendste eindklanten", styles["h3"]))
    story.append(make_table(
        ["Bedrijf", "Sector", "SAP-voetafdruk", "Betrouwbaarheid"],
        EINDKLANTEN,
        [3.3 * cm, 2.8 * cm, 8.5 * cm, 2.4 * cm],
        styles,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(EINDKLANTEN_LETOP, styles["note"]))

    story.append(PageBreak())
    story.append(Paragraph("1b. Uitgebreide lijst — aanvullende geverifieerde eindklanten per sector", styles["h3"]))
    story.append(make_table(
        ["Bedrijf", "Sector", "SAP-voetafdruk", "Betrouwbaarheid"],
        EINDKLANTEN_UITGEBREID,
        [3.5 * cm, 2.2 * cm, 9.0 * cm, 2.3 * cm],
        styles,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(EINDKLANTEN_UITGEBREID_NOTE, styles["note"]))

    story.append(PageBreak())
    story.append(Paragraph("1c. Ruwe, ongeverifieerde bulklijst (appendix)", styles["h3"]))
    story.append(Paragraph(BULK_APPENDIX_INTRO, styles["body"]))
    story.append(make_table(
        ["SAP-product", "Aantal bedrijven (NL)"],
        BULK_APPENDIX_COUNTS,
        [9 * cm, 8 * cm],
        styles,
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(BULK_APPENDIX_NAMES, styles["body"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(BULK_APPENDIX_GAPS, styles["note"]))

    story.append(PageBreak())

    # 2. Consultancy- en implementatiepartners
    story.append(Paragraph("2. Consultancy- en implementatiepartners", styles["h2"]))
    story.append(Paragraph("2a. Wereldwijde spelers (Platinum-tier, actief in NL)", styles["h3"]))
    story.append(make_table(
        ["Bedrijf", "Tier", "NL-notities"],
        SI_GLOBAAL,
        [3.5 * cm, 3.5 * cm, 9.5 * cm],
        styles,
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("2b. Middelgrote / boutique NL-spelers", styles["h3"]))
    story.append(make_table(
        ["Bedrijf", "Geverifieerd?", "Notities"],
        SI_BOUTIQUE,
        [3.5 * cm, 3.5 * cm, 9.5 * cm],
        styles,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(SI_ONBEVESTIGD, styles["note"]))

    story.append(PageBreak())

    # 3. ISVs
    story.append(Paragraph("3. Softwareontwikkelaars / ISV's op SAP/BTP", styles["h2"]))
    story.append(make_table(
        ["Bedrijf", "Geverifieerd?", "Notities"],
        ISV_LIJST,
        [3.5 * cm, 3.5 * cm, 9.5 * cm],
        styles,
    ))
    story.append(Paragraph(
        "De ISV/add-on-laag is het minst goed gedocumenteerd van de drie categorieën via publieke "
        "webresearch — een gerichte zoekactie in de SAP Store (store.sap.com), gefilterd op "
        "Nederlandse uitgevers, zou een vollediger beeld geven.",
        styles["note"],
    ))
    story.append(Spacer(1, 10))

    # 4. Partnertiers
    story.append(Paragraph("4. SAP-partnertiers en marktaandeel-signalen", styles["h2"]))
    story.append(ListFlowable(
        [ListItem(Paragraph(t, styles["body"])) for t in PARTNERTIERS],
        bulletType="bullet",
    ))

    story.append(PageBreak())

    # 5. Financiele gezondheid
    story.append(Paragraph("5. Financiële gezondheid — signalen", styles["h2"]))
    for naam, tekst in FINANCIELE_GEZONDHEID:
        story.append(Paragraph(f"<b>{naam}</b>", styles["h3"]))
        story.append(Paragraph(tekst, styles["body"]))
    story.append(Paragraph(FIN_NOTE, styles["note"]))
    story.append(Spacer(1, 10))

    # 6. Werving
    story.append(Paragraph("6. Wervingsmodellen: vast, consultancy, freelance/ZZP", styles["h2"]))
    story.append(ListFlowable(
        [ListItem(Paragraph(t, styles["body"])) for t in WERVING_TEKST],
        bulletType="bullet",
    ))
    story.append(Paragraph("Indicatieve tarieven en salarissen", styles["h3"]))
    story.append(make_table(
        ["Categorie", "Indicatie"],
        TARIEVEN,
        [8.5 * cm, 8 * cm],
        styles,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(TARIEVEN_NOTE, styles["note"]))

    story.append(PageBreak())

    # 7. Consultant rollen
    story.append(Paragraph("7. Consultantrollen en type inzet", styles["h2"]))
    for naam, tekst in CONSULTANT_ROLLEN:
        story.append(Paragraph(f"<b>{naam}</b>", styles["h3"]))
        story.append(Paragraph(tekst, styles["body"]))
    story.append(Paragraph(ROLLEN_NOTE, styles["note"]))

    story.append(PageBreak())

    # 8. Productlandschap
    story.append(Paragraph("8. SAP-productlandschap — referentie", styles["h2"]))
    story.append(make_table(
        ["Product", "Beschrijving"],
        PRODUCTLANDSCHAP,
        [4.5 * cm, 12 * cm],
        styles,
    ))

    story.append(PageBreak())

    # 9. Nieuwe ontwikkelingen
    story.append(Paragraph("9. Nieuwe ontwikkelingen bij SAP (2025-2026)", styles["h2"]))
    story.append(ListFlowable(
        [ListItem(Paragraph(t, styles["body"])) for t in NIEUWE_ONTWIKKELINGEN],
        bulletType="bullet",
    ))

    story.append(PageBreak())

    # 10. Contacten per bedrijf
    story.append(Paragraph("10. Contactkanalen en relevante functies per bedrijf", styles["h2"]))
    story.append(Paragraph(CONTACTS_NOTE, styles["note"]))
    story.append(Paragraph("10a. Eindklanten", styles["h3"]))
    story.append(make_table(
        ["Bedrijf", "Contactkanaal &amp; vacatures", "Relevante functie/afdeling"],
        CONTACTS_EINDKLANTEN,
        [3.3 * cm, 9.0 * cm, 5.5 * cm],
        styles,
    ))
    story.append(PageBreak())
    story.append(Paragraph("10b. Wereldwijde consultancy's/SI's", styles["h3"]))
    story.append(make_table(
        ["Bedrijf", "Contactkanaal &amp; vacatures", "Relevante functie/afdeling"],
        CONTACTS_SI_GLOBAAL,
        [3.3 * cm, 9.0 * cm, 5.5 * cm],
        styles,
    ))
    story.append(PageBreak())
    story.append(Paragraph("10c. NL boutique-consultancy's", styles["h3"]))
    story.append(make_table(
        ["Bedrijf", "Contactkanaal &amp; vacatures", "Relevante functie/afdeling"],
        CONTACTS_SI_BOUTIQUE,
        [3.3 * cm, 9.0 * cm, 5.5 * cm],
        styles,
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("10d. ISV's", styles["h3"]))
    story.append(make_table(
        ["Bedrijf", "Contactkanaal &amp; vacatures", "Relevante functie/afdeling"],
        CONTACTS_ISV,
        [3.3 * cm, 9.0 * cm, 5.5 * cm],
        styles,
    ))

    story.append(PageBreak())

    # 11. Recruitment agencies
    story.append(Paragraph("11. Werving- en uitzendbureaus voor SAP-talent", styles["h2"]))
    story.append(make_table(
        ["Bureau", "Specialisatie", "Gekoppelde klanten / notities"],
        RECRUITMENT_BUREAUS,
        [4.0 * cm, 5.8 * cm, 8.0 * cm],
        styles,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(RECRUITMENT_NOTE, styles["note"]))

    story.append(Spacer(1, 10))

    # 12. Hiaten
    story.append(Paragraph("12. Belangrijkste hiaten in dit onderzoek", styles["h2"]))
    story.append(ListFlowable(
        [ListItem(Paragraph(t, styles["body"])) for t in HIATEN],
        bulletType="bullet",
    ))

    story.append(Spacer(1, 16))
    story.append(Paragraph(DISCLAIMER, styles["small"]))

    doc.build(story)


def main():
    build_pdf()
    print(f"PDF-rapport opgeslagen op: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    main()

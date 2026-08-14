#!/usr/bin/env python3
"""
Multiple-choice option catalogs used by questionnaire.py.
First cut is SAP-product-centric; extend these lists as the template
grows beyond SAP-only engagements.
"""

ENGAGEMENT_TYPES = [
    "Greenfield - new company / start-up",
    "Existing enterprise transformation",
    "Merger or acquisition integration",
    "Divestiture / carve-out",
    "Template / reference architecture only",
]

INDUSTRIES = [
    "Manufacturing (Discrete)",
    "Manufacturing (Process / Chemicals)",
    "Retail & Consumer Products",
    "Utilities & Energy",
    "Financial Services & Insurance",
    "Public Sector & Government",
    "Life Sciences & Healthcare",
    "Automotive",
    "Professional Services",
    "Telecommunications",
    "Other",
]

COMPANY_SIZES = [
    "Small (< 250 employees)",
    "Mid-size (250 - 2,500 employees)",
    "Large (2,500 - 10,000 employees)",
    "Enterprise (10,000+ employees)",
]

GEO_SCOPES = [
    "Single country / single site",
    "Multi-site, single country",
    "Multi-country regional",
    "Global",
]

CURRENT_ERP_LANDSCAPE = [
    "SAP ECC 6.0 (on-premise)",
    "SAP S/4HANA (on-premise)",
    "SAP S/4HANA Cloud, private edition",
    "SAP S/4HANA Cloud, public edition",
    "Non-SAP ERP (e.g. Oracle, Microsoft Dynamics, Infor)",
    "Multiple disparate ERPs across business units",
    "No formal ERP (spreadsheets / manual)",
    "Legacy mainframe / custom-built systems",
]

PAIN_POINTS = [
    "High total cost of ownership / maintenance",
    "SAP ECC end of mainstream maintenance (2027/2030)",
    "Data silos across business units",
    "Manual / paper-based processes",
    "Lack of real-time reporting & analytics",
    "Compliance & audit risk",
    "Security / identity & access management gaps",
    "Poor user experience / adoption",
    "Shadow IT & disparate point solutions",
    "M&A integration complexity",
    "Inflexible / heavily customized core system",
    "Limited scalability for growth",
]

DRIVERS = [
    "Cost reduction & operational efficiency",
    "Regulatory / legal compliance",
    "Business agility & speed to market",
    "Customer experience improvement",
    "Digital transformation",
    "Sustainability / ESG reporting",
    "Risk reduction & resilience",
    "Growth via mergers & acquisitions",
    "Innovation & AI adoption",
    "Talent attraction & retention",
]

PRINCIPLES = [
    "Cloud-first",
    "Standardize before customize (fit-to-standard)",
    "Single source of truth for master data",
    "API-led / event-driven integration",
    "Security & privacy by design",
    "Business-driven, IT-enabled",
    "Reuse before buy before build",
    "Composable, modular architecture",
]

BUSINESS_PROCESSES = [
    "Lead-to-Cash",
    "Order-to-Cash",
    "Procure-to-Pay",
    "Record-to-Report",
    "Hire-to-Retire",
    "Plan-to-Produce",
    "Design-to-Operate",
    "Acquire-to-Decommission (Asset Management)",
    "Idea-to-Market",
    "Forecast-to-Deliver (Supply Chain)",
]

SAP_APPLICATIONS = [
    "SAP S/4HANA Cloud, public edition",
    "SAP S/4HANA Cloud, private edition",
    "SAP S/4HANA (on-premise)",
    "SAP SuccessFactors (HCM)",
    "SAP Ariba (Procurement)",
    "SAP Business Network",
    "SAP Concur (Travel & Expense)",
    "SAP Customer Experience (CX)",
    "SAP Integrated Business Planning (IBP)",
    "SAP Extended Warehouse Management (EWM)",
    "SAP Transportation Management (TM)",
    "SAP Analytics Cloud (SAC)",
    "SAP Datasphere",
    "SAP Master Data Governance (MDG)",
    "SAP Integration Suite",
    "SAP Build (low-code / process automation)",
    "SAP Fieldglass (external workforce)",
]

PLATFORM_PRIMARY = [
    "RISE with SAP (S/4HANA Cloud, private edition - managed)",
    "GROW with SAP (S/4HANA Cloud, public edition)",
    "SAP on customer-managed hyperscaler (BYOL)",
    "SAP on-premise data center",
    "Hybrid (on-premise + cloud)",
]

BTP_SERVICES = [
    "SAP Integration Suite",
    "SAP Extension Suite (ABAP Cloud / CAP)",
    "SAP Build Apps / Process Automation",
    "AI Foundation / Generative AI Hub",
    "Identity Authentication & Provisioning Services",
    "SAP Datasphere",
    "SAP Analytics Cloud",
]

HYPERSCALERS = [
    "Amazon Web Services (AWS)",
    "Microsoft Azure",
    "Google Cloud Platform (GCP)",
    "SAP-managed infrastructure only",
    "No preference / to be decided",
]

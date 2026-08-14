#!/usr/bin/env python3
"""
Single source of truth for the TOGAF ADM phase -> deliverable mapping.

Mirrors the structure found in the two existing repositories under
C:\\Archimate Repository (SAP Centralized IAM Repository, SAP Enterprise
Repository): each project gets a "Documentation" folder (core numbered
docs 01-08 plus TOGAF_Catalog_<CODE>_... artifact docs) and a "Models"
folder (one master ArchiMate XML plus one XML per ADM phase).

doc entries are tuples: (kind, key, title)
  kind "core"    -> filename "{NN}_{key}.docx", no project prefix
  kind "catalog" -> filename "TOGAF_Catalog_{SHORT_CODE}_{key}.docx"
"""

TOGAF_PHASES = [
    {
        "id": "Preliminary",
        "title": "Preliminary Phase",
        "model_suffix": "Preliminary_Phase",
        "docs": [
            ("catalog", "Prelim_Request_for_Architecture_Work", "Request for Architecture Work"),
            ("catalog", "Prelim_Organizational_Model_for_EA", "Organizational Model for Enterprise Architecture"),
            ("catalog", "Prelim_Tailored_Architecture_Framework", "Tailored Architecture Framework"),
            ("catalog", "Prelim_Architecture_Repository", "Architecture Repository"),
            ("catalog", "Prelim_Business_Principles_Goals_and_Drivers", "Business Principles, Goals and Drivers"),
            ("catalog", "Prelim_Architecture_Principles", "Architecture Principles"),
        ],
    },
    {
        "id": "A",
        "title": "Phase A - Architecture Vision",
        "model_suffix": "Phase_A_-_Architecture_Vision",
        "docs": [
            ("core", "01_Architecture_Vision", "Architecture Vision"),
            ("catalog", "A_Statement_of_Architecture_Work", "Statement of Architecture Work"),
            ("catalog", "A_Capability_Assessment", "Capability Assessment"),
            ("catalog", "A_Communications_Plan", "Communications Plan"),
            ("catalog", "A_Architecture_Definition_Document", "Architecture Definition Document (draft)"),
        ],
    },
    {
        "id": "B",
        "title": "Phase B - Business Architecture",
        "model_suffix": "Phase_B_-_Business_Architecture",
        "docs": [
            ("core", "02_Business_Architecture", "Business Architecture"),
        ],
    },
    {
        "id": "C",
        "title": "Phase C - Information Systems Architectures",
        "model_suffix": None,  # two models for this phase, handled explicitly below
        "model_suffixes": ["Phase_C_-_Data_Architecture", "Phase_C_-_Application_Architecture"],
        "docs": [
            ("core", "03_Data_Architecture", "Data Architecture"),
            ("core", "04_Application_Architecture", "Application Architecture"),
            ("catalog", "CD_Architecture_Deliverables_Phases_C_and_D", "Architecture Deliverables - Phases C and D"),
        ],
    },
    {
        "id": "D",
        "title": "Phase D - Technology Architecture",
        "model_suffix": "Phase_D_-_Technology_Architecture",
        "docs": [
            ("core", "05_Technology_Architecture", "Technology Architecture"),
        ],
    },
    {
        "id": "E",
        "title": "Phase E - Opportunities and Solutions",
        "model_suffix": "Phase_E_-_Opportunities_and_Solutions",
        "docs": [
            ("core", "06_Architecture_Requirements_Specification", "Architecture Requirements Specification"),
            ("catalog", "E_Architecture_Building_Blocks", "Architecture Building Blocks"),
            ("catalog", "E_Solution_Building_Blocks", "Solution Building Blocks"),
            ("catalog", "E_Opportunities_and_Solutions_Assessment", "Opportunities & Solutions Assessment"),
            ("catalog", "E_Architecture_Definition_Document", "Architecture Definition Document (formal)"),
        ],
    },
    {
        "id": "F",
        "title": "Phase F - Migration Planning",
        "model_suffix": "Phase_F_-_Migration_Planning",
        "docs": [
            ("core", "07_Implementation_and_Migration_Plan", "Implementation and Migration Plan"),
            ("catalog", "F_Architecture_Contract", "Architecture Contract"),
        ],
    },
    {
        "id": "G",
        "title": "Phase G - Implementation Governance",
        "model_suffix": "Phase_G_-_Implementation_Governance",
        "docs": [
            ("core", "08_Architecture_Roadmap", "Architecture Roadmap"),
            ("catalog", "G_Implementation_Governance_Model", "Implementation Governance Model"),
            ("catalog", "G_Compliance_Assessment", "Compliance Assessment Report"),
        ],
    },
    {
        "id": "H",
        "title": "Phase H - Architecture Change Management",
        "model_suffix": "Phase_H_-_Architecture_Change_Management",
        "docs": [
            ("catalog", "H_Requirements_Impact_Assessment", "Requirements Impact Assessment"),
            ("catalog", "H_Change_Request", "Change Request"),
        ],
    },
]


def doc_filename(kind: str, key: str, short_code: str) -> str:
    if kind == "core":
        return f"{key}.docx"
    return f"TOGAF_Catalog_{short_code}_{key}.docx"


def model_filename(slug: str, suffix: str | None) -> str:
    if suffix is None:
        return f"{slug}.xml"
    return f"{slug}_{suffix}.xml"

#!/usr/bin/env python3
"""
Builds ArchiMate 3.x Model Exchange File (.xml) skeletons, importable
directly into Archi, pre-filled with elements derived from questionnaire
answers. Matches the schema used in the existing repositories under
C:\\Archimate Repository (xmlns .../xsd/archimate/3.0/).

Element identifiers are assigned once per conceptual element (see Registry)
and reused across the master model and every phase model, so phase files
stay cross-referenceable against the master - mirrors the convention used
in the existing SAP Enterprise / IAM repositories.
"""

from datetime import date
from xml.sax.saxutils import escape

NS = 'xmlns="http://www.opengroup.org/xsd/archimate/3.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengroup.org/xsd/archimate/3.0/ http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd"'


class Registry:
    """Assigns a stable id per (prefix, name) so the same conceptual
    element gets the same identifier in every model file it appears in."""

    def __init__(self):
        self._map = {}
        self._counters = {}

    def id_for(self, prefix: str, name: str) -> str:
        key = (prefix, name)
        if key not in self._map:
            self._counters[prefix] = self._counters.get(prefix, 0) + 1
            self._map[key] = f"{prefix}{self._counters[prefix]}"
        return self._map[key]


def _element_xml(el: dict) -> str:
    identifier = el["id"]
    etype = el["type"]
    name = escape(el["name"])
    doc = el.get("doc")
    props = el.get("props") or {}

    inner = [f'      <name xml:lang="en">{name}</name>']
    if doc:
        inner.append(f'      <documentation xml:lang="en">{escape(doc)}</documentation>')
    if props:
        inner.append("      <properties>")
        for label, value in props.items():
            inner.append(
                f'        <property propertyDefinitionRef="propdef-{label}">'
                f'<value xml:lang="en">{escape(str(value))}</value></property>'
            )
        inner.append("      </properties>")
    body = "\n".join(inner)
    return f'    <element identifier="{identifier}" xsi:type="{etype}">\n{body}\n    </element>'


def build_model_xml(identifier: str, name: str, documentation: str, elements: list) -> str:
    els_xml = "\n".join(_element_xml(e) for e in elements)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<model {NS} identifier="{identifier}">
  <name xml:lang="en">{escape(name)}</name>
  <documentation xml:lang="en">{escape(documentation)}</documentation>
  <elements>
{els_xml}
  </elements>
</model>
"""


# ---------------------------------------------------------------------------
# Element derivation from questionnaire answers
# ---------------------------------------------------------------------------

CORE_STAKEHOLDERS = ["CIO", "CFO", "COO", "Chief Enterprise Architect", "Program Sponsor"]


def build_elements(reg: Registry, answers: dict) -> dict:
    """Returns a dict of category -> list of element dicts, built once and
    shared across the master model and every phase model."""

    stakeholders = [
        {"id": reg.id_for("stake", n), "type": "Stakeholder", "name": n}
        for n in CORE_STAKEHOLDERS
    ]
    for proc in answers.get("business_processes", []):
        name = f"Business Process Owner - {proc}"
        stakeholders.append({"id": reg.id_for("stake", name), "type": "Stakeholder", "name": name})

    drivers = [
        {"id": reg.id_for("drv", d), "type": "Driver", "name": d}
        for d in answers.get("drivers", [])
    ]
    goals = [
        {"id": reg.id_for("goal", d), "type": "Goal", "name": f"Achieve: {d}", "doc": f"Realizes driver '{d}'."}
        for d in answers.get("drivers", [])
    ]
    principles = [
        {"id": reg.id_for("prin", p), "type": "Principle", "name": p}
        for p in answers.get("principles", [])
    ]
    assessments = [
        {"id": reg.id_for("assess", p), "type": "Assessment", "name": p, "doc": "Identified during current-state analysis."}
        for p in answers.get("pain_points", [])
    ]
    requirements = [
        {"id": reg.id_for("req", p), "type": "Requirement", "name": f"Resolve: {p}"}
        for p in answers.get("pain_points", [])
    ]
    capabilities = [
        {
            "id": reg.id_for("cap", p),
            "type": "Capability",
            "name": p,
            "doc": "Strategic business capability in scope for this engagement.",
            "props": {"maturity": "To be assessed"},
        }
        for p in answers.get("business_processes", [])
    ]
    business_processes = [
        {"id": reg.id_for("bp", p), "type": "BusinessProcess", "name": p}
        for p in answers.get("business_processes", [])
    ]
    data_objects = [
        {"id": reg.id_for("dobj", p), "type": "DataObject", "name": f"{p} Data"}
        for p in answers.get("business_processes", [])
    ]
    applications = [
        {"id": reg.id_for("app", a), "type": "ApplicationComponent", "name": a}
        for a in answers.get("applications", [])
    ]

    technology = []
    platform_primary = answers.get("platform_primary")
    if platform_primary:
        technology.append({"id": reg.id_for("tech", platform_primary), "type": "Node", "name": platform_primary})
    for svc in answers.get("btp_services", []):
        technology.append({"id": reg.id_for("tech", svc), "type": "TechnologyService", "name": svc})
    hyperscaler = answers.get("hyperscaler")
    if hyperscaler and "No preference" not in hyperscaler:
        technology.append({"id": reg.id_for("tech", hyperscaler), "type": "Node", "name": hyperscaler})

    work_packages = [
        {"id": reg.id_for("wp", d), "type": "WorkPackage", "name": f"Implement: {d}"}
        for d in answers.get("drivers", [])
    ]
    plateau_baseline = {"id": reg.id_for("plat", "Baseline Architecture"), "type": "Plateau", "name": "Baseline Architecture"}
    plateau_target = {"id": reg.id_for("plat", "Target Architecture"), "type": "Plateau", "name": "Target Architecture"}
    gap = {"id": reg.id_for("gap", "Gap Analysis"), "type": "Gap", "name": "Gap Analysis"}
    change_log = {"id": reg.id_for("deliv", "Change Request Log"), "type": "Deliverable", "name": "Change Request Log"}

    return {
        "stakeholders": stakeholders,
        "drivers": drivers,
        "goals": goals,
        "principles": principles,
        "assessments": assessments,
        "requirements": requirements,
        "capabilities": capabilities,
        "business_processes": business_processes,
        "data_objects": data_objects,
        "applications": applications,
        "technology": technology,
        "work_packages": work_packages,
        "plateaus": [plateau_baseline, plateau_target],
        "gap": [gap],
        "change_log": [change_log],
    }


def elements_for_phase(phase_id: str, cats: dict) -> list:
    if phase_id == "Preliminary":
        return cats["stakeholders"][: len(CORE_STAKEHOLDERS)] + cats["principles"]
    if phase_id == "A":
        return cats["stakeholders"] + cats["drivers"] + cats["goals"] + cats["capabilities"]
    if phase_id == "B":
        return cats["business_processes"] + cats["stakeholders"][len(CORE_STAKEHOLDERS):]
    if phase_id == "C-data":
        return cats["data_objects"]
    if phase_id == "C-app":
        return cats["applications"]
    if phase_id == "D":
        return cats["technology"]
    if phase_id == "E":
        return cats["requirements"] + cats["plateaus"] + cats["gap"]
    if phase_id == "F":
        return cats["work_packages"]
    if phase_id == "G":
        return cats["principles"] + [cats["plateaus"][1]]
    if phase_id == "H":
        return cats["requirements"] + cats["change_log"]
    return []


def master_elements(cats: dict) -> list:
    seen = {}
    ordered = []
    for group in cats.values():
        for el in group:
            if el["id"] not in seen:
                seen[el["id"]] = True
                ordered.append(el)
    return ordered


def documentation_header(answers: dict, phase_title: str | None = None) -> str:
    base = f"Author: {answers.get('author', '')}; Generated: {date.today().isoformat()}. "
    base += f"{answers.get('repository_name', '')} for {answers.get('company_name', '')}, structured per the TOGAF ADM."
    if phase_title:
        base += f" Phase-scoped extract for {phase_title}."
    return base

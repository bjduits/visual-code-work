#!/usr/bin/env python3
"""
Validates every ArchiMate Model Exchange File (.xml) under ../projects/*/Models/
and reports errors and warnings: malformed XML, duplicate identifiers,
elements missing a name, unrecognized xsi:type values, relationships with
dangling source/target references, properties that reference an
undeclared propertyDefinitionRef, model children out of the schema's
required order (e.g. a <propertyDefinitions> block placed before <elements>,
which parses fine but Archi's importer rejects at import time), and view
node x/y/w/h values that aren't valid xsd:integer (e.g. "200.0" from
unrounded layout math).

Usage:
    python validate_models.py                  # validate every project
    python validate_models.py "SAP Enterprise Repository"   # one project only
    python validate_models.py --fix             # also auto-fix what's safely fixable
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECTS_DIR = Path(__file__).parent.parent / "projects"
ARCHIMATE_NS = "http://www.opengroup.org/xsd/archimate/3.0/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

# ArchiMate 3.2 standard element/relationship type names, across all layers.
KNOWN_TYPES = {
    # Business
    "BusinessActor", "BusinessRole", "BusinessCollaboration", "BusinessInterface",
    "BusinessProcess", "BusinessFunction", "BusinessInteraction", "BusinessEvent",
    "BusinessService", "BusinessObject", "Contract", "Representation", "Product",
    # Application
    "ApplicationComponent", "ApplicationCollaboration", "ApplicationInterface",
    "ApplicationFunction", "ApplicationInteraction", "ApplicationProcess",
    "ApplicationEvent", "ApplicationService", "DataObject",
    # Technology (incl. physical)
    "Node", "Device", "SystemSoftware", "TechnologyCollaboration",
    "TechnologyInterface", "Path", "CommunicationNetwork", "TechnologyFunction",
    "TechnologyProcess", "TechnologyInteraction", "TechnologyEvent",
    "TechnologyService", "Artifact", "Equipment", "Facility",
    "DistributionNetwork", "Material",
    # Motivation
    "Stakeholder", "Driver", "Assessment", "Goal", "Outcome", "Principle",
    "Requirement", "Constraint", "Meaning", "Value",
    # Strategy
    "Resource", "Capability", "CourseOfAction", "ValueStream",
    # Implementation & Migration
    "WorkPackage", "Deliverable", "ImplementationEvent", "Plateau", "Gap",
    # Other / composite
    "Location", "Grouping", "Junction",
    # Relationships
    "Composition", "Aggregation", "Assignment", "Realization", "Serving",
    "Access", "Influence", "Triggering", "Flow", "Specialization", "Association",
}


def qn(tag: str) -> str:
    return f"{{{ARCHIMATE_NS}}}{tag}"


def xsi_type(elem) -> str | None:
    return elem.get(f"{{{XSI_NS}}}type")


def validate_file(path: Path) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []

    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        errors.append(f"not well-formed XML: {e}")
        return errors, warnings

    root = tree.getroot()
    if root.tag != qn("model"):
        warnings.append(f"root element is <{root.tag}>, expected <model> in the ArchiMate 3.0 namespace")

    # The Model Exchange File schema requires model children in exactly this
    # order; anything out of sequence (e.g. propertyDefinitions before
    # elements) parses fine with ElementTree but Archi's schema-validating
    # importer rejects it with a cvc-complex-type.2.4.a error.
    schema_order = ["name", "documentation", "properties", "elements", "relationships",
                     "organizations", "propertyDefinitions", "views"]
    seen_tags = [c.tag.split("}")[-1] for c in root if c.tag.split("}")[-1] in schema_order]
    expected = [tag for tag in schema_order if tag in seen_tags]
    if seen_tags != expected:
        errors.append(
            f"model children out of schema order: found {seen_tags}, expected {expected} "
            "(will fail Archi's import validation)"
        )

    elements_root = root.find(qn("elements"))
    relationships_root = root.find(qn("relationships"))
    propdefs_root = root.find(qn("propertyDefinitions"))

    element_ids = set()
    all_ids = set()
    declared_propdefs = set()

    if propdefs_root is not None:
        for pd in propdefs_root.findall(qn("propertyDefinition")):
            declared_propdefs.add(pd.get("identifier"))

    def register_id(identifier, kind):
        if identifier in all_ids:
            errors.append(f"duplicate identifier '{identifier}' ({kind})")
        all_ids.add(identifier)

    if elements_root is not None:
        for el in elements_root.findall(qn("element")):
            ident = el.get("identifier")
            register_id(ident, "element")
            element_ids.add(ident)

            name_el = el.find(qn("name"))
            if name_el is None or not (name_el.text or "").strip():
                errors.append(f"element '{ident}' has no <name>")

            etype = xsi_type(el)
            if not etype:
                errors.append(f"element '{ident}' has no xsi:type")
            elif etype not in KNOWN_TYPES:
                warnings.append(f"element '{ident}' has unrecognized xsi:type '{etype}' (possible typo)")

            props_root = el.find(qn("properties"))
            if props_root is not None:
                for prop in props_root.findall(qn("property")):
                    ref = prop.get("propertyDefinitionRef")
                    if ref and ref not in declared_propdefs:
                        errors.append(
                            f"element '{ident}' property references undeclared propertyDefinitionRef '{ref}'"
                        )

    if relationships_root is not None:
        for rel in relationships_root.findall(qn("relationship")):
            ident = rel.get("identifier")
            register_id(ident, "relationship")
            src, tgt = rel.get("source"), rel.get("target")
            if src and src not in element_ids:
                warnings.append(f"relationship '{ident}' source '{src}' not defined as an element in this file")
            if tgt and tgt not in element_ids:
                warnings.append(f"relationship '{ident}' target '{tgt}' not defined as an element in this file")

    # <node>/<connection> x/y/w/h are xsd:integer per the schema - a float
    # like "200.0" parses fine with ElementTree but Archi's schema-validating
    # importer rejects it (cvc-datatype-valid.1.2.1). Easy to introduce via
    # any layout math that isn't explicitly rounded/int-cast (e.g. an
    # average), so check every view node/connection's coordinates directly.
    views_root = root.find(qn("views"))
    if views_root is not None:
        diagrams_root = views_root.find(qn("diagrams"))
        if diagrams_root is not None:
            for view in diagrams_root.findall(qn("view")):
                for node in view.iter(qn("node")):
                    node_id = node.get("identifier")
                    for attr in ("x", "y", "w", "h"):
                        val = node.get(attr)
                        if val is not None and not val.lstrip("-").isdigit():
                            errors.append(f"view node '{node_id}' has non-integer {attr}='{val}' (will fail Archi's import validation)")

    return errors, warnings


def fix_file(path: Path) -> bool:
    """Auto-fixes two safely-mechanical issues:
    1. A property referencing an undeclared propertyDefinitionRef - adds a
       minimal <propertyDefinitions> entry (friendly name derived from the id)
       rather than removing data.
    2. model children out of the schema's required order (e.g. a misplaced
       <propertyDefinitions> block) - reorders them in place.
    Returns True if the file was changed."""
    tree = ET.parse(path)
    root = tree.getroot()
    ET.register_namespace("", ARCHIMATE_NS)
    ET.register_namespace("xsi", XSI_NS)

    propdefs_root = root.find(qn("propertyDefinitions"))
    declared = set()
    if propdefs_root is not None:
        declared = {pd.get("identifier") for pd in propdefs_root.findall(qn("propertyDefinition"))}

    used_refs = set()
    elements_root = root.find(qn("elements"))
    if elements_root is not None:
        for el in elements_root.findall(qn("element")):
            props_root = el.find(qn("properties"))
            if props_root is not None:
                for prop in props_root.findall(qn("property")):
                    ref = prop.get("propertyDefinitionRef")
                    if ref:
                        used_refs.add(ref)

    missing = sorted(used_refs - declared)

    # The Model Exchange File schema requires model children in this order:
    # name, documentation, properties, elements, relationships, organizations,
    # propertyDefinitions, views. Rebuild root children in that sequence
    # unconditionally - cheap, idempotent, and a misplaced (rather than
    # missing) propertyDefinitions block is exactly what breaks import into
    # Archi even when no propertyDefinitionRef is actually missing.
    order = ["name", "documentation", "properties", "elements", "relationships",
             "organizations", "propertyDefinitions", "views"]
    current = [c.tag.split("}")[-1] for c in root if c.tag.split("}")[-1] in order]
    needs_reorder = current != [tag for tag in order if tag in current]

    if not missing and not needs_reorder:
        return False

    if propdefs_root is None and missing:
        propdefs_root = ET.SubElement(root, qn("propertyDefinitions"))

    children = {c.tag.split("}")[-1]: c for c in list(root)}
    for c in list(root):
        root.remove(c)
    for tag in order:
        if tag in children:
            root.append(children[tag])

    for ref in missing:
        friendly = ref.replace("propdef-", "").replace("-", " ").replace("_", " ").title()
        pd = ET.SubElement(propdefs_root, qn("propertyDefinition"))
        pd.set("identifier", ref)
        pd.set("type", "string")
        name_el = ET.SubElement(pd, qn("name"))
        name_el.set("{http://www.w3.org/XML/1998/namespace}lang", "en")
        name_el.text = friendly

    tree.write(path, encoding="UTF-8", xml_declaration=True)
    return True


def main():
    args = [a for a in sys.argv[1:] if a != "--fix"]
    do_fix = "--fix" in sys.argv[1:]

    if args:
        project_dirs = [PROJECTS_DIR / args[0]]
    else:
        project_dirs = sorted(p for p in PROJECTS_DIR.iterdir() if p.is_dir())

    total_errors = 0
    total_warnings = 0
    total_fixed = 0

    for project_dir in project_dirs:
        models_dir = project_dir / "Models"
        if not models_dir.is_dir():
            continue
        print(f"\n{project_dir.name}")
        print("=" * len(project_dir.name))
        for xml_path in sorted(models_dir.glob("*.xml")):
            errors, warnings = validate_file(xml_path)
            if do_fix and errors:
                if fix_file(xml_path):
                    total_fixed += 1
                    errors, warnings = validate_file(xml_path)  # re-check after fixing

            status = "OK" if not errors and not warnings else ("ERROR" if errors else "WARN")
            print(f"  [{status}] {xml_path.name}")
            for e in errors:
                print(f"      ERROR:   {e}")
            for w in warnings:
                print(f"      WARNING: {w}")
            total_errors += len(errors)
            total_warnings += len(warnings)

    print(f"\n{total_errors} error(s), {total_warnings} warning(s) across {sum(1 for _ in PROJECTS_DIR.glob('*/Models/*.xml')) if not args else len(list((PROJECTS_DIR / args[0] / 'Models').glob('*.xml')))} file(s).")
    if do_fix:
        print(f"Auto-fixed {total_fixed} file(s) (undeclared propertyDefinitionRef and/or out-of-order model children).")
    if total_errors and not do_fix:
        print("Re-run with --fix to auto-fix what's safely fixable.")


if __name__ == "__main__":
    main()

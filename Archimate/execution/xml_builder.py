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


def _relationship_xml(r: dict) -> str:
    name_part = f'\n      <name xml:lang="en">{escape(r["name"])}</name>' if r.get("name") else ""
    return (f'    <relationship identifier="{r["id"]}" source="{r["source"]}" target="{r["target"]}" '
            f'xsi:type="{r["type"]}">{name_part}\n    </relationship>')


def _relationships_xml(relationships: list) -> str:
    if not relationships:
        return ""
    entries = "\n".join(_relationship_xml(r) for r in relationships)
    return f"  <relationships>\n{entries}\n  </relationships>\n"


def _property_defs_xml(elements: list) -> str:
    """Every element that carries a propertyDefinitionRef must have a matching
    declaration in propertyDefinitions, or the file fails validation (see
    validate_models.py). Auto-derive the declarations from what's actually
    used, so this can't drift out of sync with the elements below."""
    used_refs = []
    for el in elements:
        for label in (el.get("props") or {}):
            ref = f"propdef-{label}"
            if ref not in used_refs:
                used_refs.append(ref)
    if not used_refs:
        return ""
    entries = "\n".join(
        f'    <propertyDefinition identifier="{ref}" type="string">'
        f'<name xml:lang="en">{escape(ref.replace("propdef-", "").replace("-", " ").replace("_", " ").title())}</name>'
        f"</propertyDefinition>"
        for ref in used_refs
    )
    return f"  <propertyDefinitions>\n{entries}\n  </propertyDefinitions>\n"


# ---------------------------------------------------------------------------
# View (diagram) auto-layout
# ---------------------------------------------------------------------------

# Column order elements are laid out in, left to right. This is a *layout*
# order, not strictly the ArchiMate layer stack - some ArchiMate layers are
# deliberately split across more than one column so that directly-related
# element types land in adjacent columns instead of a genuinely unrelated
# column sitting between them (e.g. Driver/Assessment "cause" elements lead,
# Goal/Requirement "effect" elements follow directly after, so their
# Influence relationship is a one-column hop instead of cutting across
# whatever else happens to be in a shared Motivation bucket). Several columns
# still map back to the same ArchiMate layer for legend/coloring purposes -
# see LAYER_TO_CANONICAL below.
LAYER_ORDER = ["Motivation-Input", "Motivation-Output", "Stakeholders", "Strategy", "Business",
               "Application", "Technology", "Gap", "Implementation & Migration", "Other"]

TYPE_LAYER = {
    "Stakeholder": "Stakeholders",
    # Motivation - split into "cause" (Input) and "effect" (Output) columns;
    # build_relationships always draws Input -> Output (Driver->Goal,
    # Assessment->Requirement), so this keeps those as a one-column hop.
    "Driver": "Motivation-Input", "Assessment": "Motivation-Input", "Principle": "Motivation-Input",
    "Constraint": "Motivation-Input", "Meaning": "Motivation-Input", "Value": "Motivation-Input",
    "Goal": "Motivation-Output", "Requirement": "Motivation-Output", "Outcome": "Motivation-Output",
    # Strategy
    "Resource": "Strategy", "Capability": "Strategy", "CourseOfAction": "Strategy", "ValueStream": "Strategy",
    # Business
    "BusinessActor": "Business", "BusinessRole": "Business", "BusinessCollaboration": "Business",
    "BusinessInterface": "Business", "BusinessProcess": "Business", "BusinessFunction": "Business",
    "BusinessInteraction": "Business", "BusinessEvent": "Business", "BusinessService": "Business",
    "BusinessObject": "Business", "Contract": "Business", "Representation": "Business", "Product": "Business",
    # Application
    "ApplicationComponent": "Application", "ApplicationCollaboration": "Application",
    "ApplicationInterface": "Application", "ApplicationFunction": "Application",
    "ApplicationInteraction": "Application", "ApplicationProcess": "Application",
    "ApplicationEvent": "Application", "ApplicationService": "Application", "DataObject": "Application",
    # Technology
    "Node": "Technology", "Device": "Technology", "SystemSoftware": "Technology",
    "TechnologyCollaboration": "Technology", "TechnologyInterface": "Technology", "Path": "Technology",
    "CommunicationNetwork": "Technology", "TechnologyFunction": "Technology", "TechnologyProcess": "Technology",
    "TechnologyInteraction": "Technology", "TechnologyEvent": "Technology", "TechnologyService": "Technology",
    "Artifact": "Technology", "Equipment": "Technology", "Facility": "Technology",
    "DistributionNetwork": "Technology", "Material": "Technology",
    # Implementation & Migration - Gap gets its own column ahead of the rest,
    # since build_relationships draws Gap -> both Plateaus; without its own
    # column that edge would cut across whatever else shares the bucket.
    "Gap": "Gap",
    "WorkPackage": "Implementation & Migration", "Deliverable": "Implementation & Migration",
    "ImplementationEvent": "Implementation & Migration", "Plateau": "Implementation & Migration",
    # Other / composite
    "Location": "Other", "Grouping": "Other", "Junction": "Other",
}

# Every layout column maps back to one of the true ArchiMate/legend layers
# for coloring purposes, even where LAYER_ORDER splits a layer into several
# layout columns (e.g. Motivation-Input/Motivation-Output/Stakeholders are
# all colored as "Motivation").
LAYER_TO_CANONICAL = {
    "Motivation-Input": "Motivation", "Motivation-Output": "Motivation", "Stakeholders": "Motivation",
    "Strategy": "Strategy", "Business": "Business", "Application": "Application", "Technology": "Technology",
    "Gap": "Implementation & Migration", "Implementation & Migration": "Implementation & Migration",
    "Other": "Other",
}

NODE_W, NODE_H = 180, 60
COL_GAP, ROW_GAP, MARGIN = 90, 20, 40

# Fill colors per true ArchiMate/legend layer, matching the LEGEND swatches
# added to every view below and the palette used throughout the existing SAP
# reference repositories' hand-built views.
LAYER_COLOR = {
    "Motivation": (204, 204, 255),
    "Strategy": (245, 222, 170),
    "Business": (255, 255, 181),
    "Application": (181, 255, 255),
    "Technology": (201, 231, 183),
    "Implementation & Migration": (255, 224, 224),
    "Other": (232, 232, 232),
}

LEGEND_ITEMS = [
    ("legend_motivation", "Motivation"),
    ("legend_strategy", "Strategy"),
    ("legend_business", "Business"),
    ("legend_application", "Application"),
    ("legend_technology", "Technology"),
    ("legend_implementation", "Implementation & Migration"),
]
LEGEND_TITLE_W, LEGEND_TITLE_H = 326, 30
SWATCH_W, SWATCH_H, SWATCH_GAP = 160, 32, 6
INFO_GAP, INFO_W, INFO_H = 54, 340, 150


def _style_xml(rgb: tuple) -> str:
    r, g, b = rgb
    return (f'\n        <style>\n'
            f'          <fillColor r="{r}" g="{g}" b="{b}"/>\n'
            f'          <lineColor r="90" g="90" b="90"/>\n'
            f'          <font name="Segoe UI" size="8"><color r="20" g="20" b="20"/></font>\n'
            f'        </style>\n      ')


def _node_xml(vnode_id: str, element_id: str, x: int, y: int, w: int, h: int, color: tuple) -> str:
    return (f'      <node identifier="{vnode_id}" xsi:type="Element" elementRef="{element_id}" '
            f'x="{x}" y="{y}" w="{w}" h="{h}">{_style_xml(color)}</node>')


def _legend_base_elements() -> list:
    """The LEGEND title + one swatch per layer, declared once per file and
    referenced (via a fresh <node>) from every view in that file - mirrors
    how the SAP reference repositories reuse a single legend_title/
    legend_<layer> element across all ~20 of their views instead of
    duplicating it per view."""
    elements = [{"id": "legend_title", "type": "Grouping", "name": "LEGEND", "doc": "Legend title."}]
    for gid, layer in LEGEND_ITEMS:
        elements.append({"id": gid, "type": "Grouping", "name": layer,
                          "doc": f"Legend swatch: elements colored like this box belong to the {layer} layer/section."})
    return elements


def _layout_elements(elements: list, relationships: list, x_start: int, counter: int):
    """Lays out `elements` into columns (LAYER_ORDER), one node per element,
    colored to match the LEGEND. From the second column onward, each element
    is positioned near the average y of whichever already-placed neighbors it
    has a relationship with (a single left-to-right barycenter pass), rather
    than just stacked top-down in list order - a naive stack put related
    elements (e.g. a capability and the stakeholder who owns it) on unrelated
    rows and produced a rat's-nest of long diagonal connector lines; this
    keeps connected elements roughly level with each other instead.
    Returns (nodes_xml_list, node_info, max_y, next_counter)."""
    columns: dict[str, list] = {}
    for el in elements:
        layer = TYPE_LAYER.get(el["type"], "Other")
        columns.setdefault(layer, []).append(el)

    adjacency: dict[str, list] = {}
    for r in relationships:
        adjacency.setdefault(r["source"], []).append(r["target"])
        adjacency.setdefault(r["target"], []).append(r["source"])

    nodes = []
    node_info: dict[str, dict] = {}  # element id -> {"vnode":, "y":}
    x = x_start
    max_y = MARGIN

    for layer in LAYER_ORDER:
        col_elements = columns.get(layer)
        if not col_elements:
            continue

        desired_y = []
        for el in col_elements:
            neighbor_ys = [node_info[n]["y"] for n in adjacency.get(el["id"], ()) if n in node_info]
            desired_y.append(sum(neighbor_ys) / len(neighbor_ys) if neighbor_ys else None)

        # Elements with a placed, related neighbor sort by that neighbor's y;
        # elements with no signal yet keep their original relative order.
        order = sorted(range(len(col_elements)),
                        key=lambda i: (desired_y[i] is None, desired_y[i] if desired_y[i] is not None else i))

        y_cursor = MARGIN
        color = LAYER_COLOR[LAYER_TO_CANONICAL.get(layer, "Other")]
        for i in order:
            el = col_elements[i]
            # desired_y[i] is a barycenter average and so can be a float (e.g.
            # 200.0); x/y/w/h are xsd:integer per the schema, so round to int
            # here or Archi's importer rejects the file (cvc-datatype-valid.1.2.1).
            y = y_cursor if desired_y[i] is None else max(y_cursor, round(desired_y[i]))
            vnode_id = f"vnode{counter}"
            counter += 1
            node_info[el["id"]] = {"vnode": vnode_id, "y": y}
            nodes.append(_node_xml(vnode_id, el["id"], x, y, NODE_W, NODE_H, color))
            y_cursor = y + NODE_H + ROW_GAP
            max_y = max(max_y, y + NODE_H)
        x += NODE_W + COL_GAP

    return nodes, node_info, max_y, counter


def _legend_and_info_nodes(nodes: list, extra_elements: list, counter: int, top_y: int,
                            view_key: str, view_name: str, phase_label: str) -> int:
    """Places a <node> for each already-declared LEGEND element plus a fresh,
    view-specific VIEW INFORMATION Grouping element/node, below the main
    diagram content. Mutates `nodes`/`extra_elements` in place; returns the
    next free vnode counter value."""
    today = date.today().isoformat()

    def place(gid: str, x: int, y: int, w: int, h: int, canonical_layer: str) -> None:
        nonlocal counter
        nodes.append(_node_xml(f"vnode{counter}", gid, x, y, w, h, LAYER_COLOR[canonical_layer]))
        counter += 1

    place("legend_title", MARGIN, top_y, LEGEND_TITLE_W, LEGEND_TITLE_H, "Other")

    swatch_top = top_y + LEGEND_TITLE_H + SWATCH_GAP
    for idx, (gid, layer) in enumerate(LEGEND_ITEMS):
        col, row = idx % 2, idx // 2
        sx = MARGIN + col * (SWATCH_W + SWATCH_GAP)
        sy = swatch_top + row * (SWATCH_H + SWATCH_GAP)
        place(gid, sx, sy, SWATCH_W, SWATCH_H, layer)

    info_id = f"viewinfo_{view_key}"
    info_text = f"VIEW INFORMATION\nView: {view_name}\nPhase: {phase_label}\nCreated: {today}\nLast Modified: {today}"
    extra_elements.append({"id": info_id, "type": "Grouping", "name": info_text, "doc": f"View metadata block for '{view_name}'."})
    info_x = MARGIN + LEGEND_TITLE_W + INFO_GAP
    place(info_id, info_x, top_y, INFO_W, INFO_H, "Other")

    return counter


def build_views_xml(view_specs: list, phase_label: str) -> tuple:
    """Builds every view for one model file. `view_specs` is a list of
    (view_key, view_name, elements, relationships) tuples - typically from
    view_specs_for_scope(). All views in a file share one LEGEND (declared
    once, referenced from every view - see _legend_base_elements) plus a
    fresh VIEW INFORMATION box per view. A <connection> is drawn for every
    relationship whose source AND target both have a node in that particular
    view (cross-view relationships are still declared in <relationships> but
    simply aren't drawn in a view that doesn't contain both ends).
    Returns (extra_elements, views_block_xml) - extra_elements (the legend
    plus every view's VIEW INFORMATION grouping) must be merged into the
    model's <elements> by the caller."""
    if not view_specs:
        return [], ""

    extra_elements = _legend_base_elements()
    node_counter = 1
    conn_counter = 1
    view_blocks = []

    for view_key, view_name, elements, relationships in view_specs:
        nodes, node_info, max_y, node_counter = _layout_elements(elements, relationships, MARGIN, node_counter)
        node_counter = _legend_and_info_nodes(nodes, extra_elements, node_counter, max_y + MARGIN,
                                               view_key, view_name, phase_label)

        connections = []
        for r in relationships:
            src = node_info.get(r["source"])
            tgt = node_info.get(r["target"])
            if src is None or tgt is None:
                continue
            connections.append(
                f'      <connection identifier="vconn{conn_counter}" xsi:type="Relationship" '
                f'relationshipRef="{r["id"]}" source="{src["vnode"]}" target="{tgt["vnode"]}"/>'
            )
            conn_counter += 1

        body_xml = "\n".join(nodes + connections)
        view_blocks.append(f"""      <view identifier="v-{view_key}" xsi:type="Diagram">
        <name xml:lang="en">{escape(view_name)}</name>
{body_xml}
      </view>""")

    views_inner = "\n".join(view_blocks)
    views_block = f"""  <views>
    <diagrams>
{views_inner}
    </diagrams>
  </views>
"""
    return extra_elements, views_block


def build_model_xml(identifier: str, name: str, documentation: str, elements: list,
                     relationships: list | None = None, view_specs: list | None = None,
                     phase_label: str = "Master Model (all phases)") -> str:
    relationships = relationships or []
    if view_specs is None:
        view_specs = [("overview", "Overview", elements, relationships)]
    extra_elements, views_xml = build_views_xml(view_specs, phase_label)
    all_elements = elements + extra_elements
    els_xml = "\n".join(_element_xml(e) for e in all_elements)
    rels_xml = _relationships_xml(relationships)
    propdefs_xml = _property_defs_xml(all_elements)
    # Model Exchange File schema requires model children in this order:
    # name, documentation, properties, elements, relationships, organizations,
    # propertyDefinitions, views, or Archi's importer rejects the file with a
    # cvc-complex-type.2.4.a error.
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<model {NS} identifier="{identifier}">
  <name xml:lang="en">{escape(name)}</name>
  <documentation xml:lang="en">{escape(documentation)}</documentation>
  <elements>
{els_xml}
  </elements>
{rels_xml}{propdefs_xml}{views_xml}</model>
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

    # "tag" isn't written to the XML (see _element_xml) - it's only used to
    # pick out sub-views like "SAP BTP" / "Integration Architecture" from the
    # technology category without fabricating a distinction the questionnaire
    # doesn't actually capture.
    technology = []
    platform_primary = answers.get("platform_primary")
    if platform_primary:
        technology.append({"id": reg.id_for("tech", platform_primary), "type": "Node", "name": platform_primary, "tag": "platform"})
    for svc in answers.get("btp_services", []):
        technology.append({"id": reg.id_for("tech", svc), "type": "TechnologyService", "name": svc, "tag": "btp"})
    hyperscaler = answers.get("hyperscaler")
    if hyperscaler and "No preference" not in hyperscaler:
        technology.append({"id": reg.id_for("tech", hyperscaler), "type": "Node", "name": hyperscaler, "tag": "hyperscaler"})

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


def build_relationships(reg: Registry, cats: dict) -> list:
    """Derives a default relationship set purely from correspondences that
    already exist in the data - same underlying answer, same list position -
    never a link between elements whose correspondence isn't actually implied
    by the questionnaire (e.g. specific applications are never wired to
    specific capabilities: those two lists come from unrelated questions, and
    guessing a pairing would assert business logic that isn't real).
    Relationship type/label conventions mirror the existing SAP Enterprise
    Repository model (e.g. Capability-Association-BusinessProcess "supports",
    Driver-Influence-Goal "+")."""
    rels = []

    def add(rtype: str, source: dict, target: dict, label: str):
        rid = reg.id_for("rel", f"{source['id']}->{target['id']}:{rtype}")
        rels.append({"id": rid, "type": rtype, "source": source["id"], "target": target["id"], "name": label})

    # Capability <-> BusinessProcess: same underlying process, same list order.
    for cap, bp in zip(cats["capabilities"], cats["business_processes"]):
        add("Association", cap, bp, "supports")

    # BusinessProcess -> its own DataObject: same underlying process.
    for bp, dobj in zip(cats["business_processes"], cats["data_objects"]):
        add("Access", bp, dobj, "accesses")

    # "Business Process Owner - X" stakeholders <-> BusinessProcess/Capability
    # X: matched by name, both built from the same business_processes answers
    # in the same order.
    process_owner_stakes = cats["stakeholders"][len(CORE_STAKEHOLDERS):]
    for stake, bp in zip(process_owner_stakes, cats["business_processes"]):
        add("Assignment", stake, bp, "owns")
    for stake, cap in zip(process_owner_stakes, cats["capabilities"]):
        add("Association", stake, cap, "has interest in")

    # Core (exec) stakeholders <-> every Goal: sponsorship / interest.
    core_stakes = cats["stakeholders"][: len(CORE_STAKEHOLDERS)]
    for stake in core_stakes:
        for goal in cats["goals"]:
            add("Association", stake, goal, "has interest in")

    # Driver -> its own Goal: same underlying driver, same list order.
    for drv, goal in zip(cats["drivers"], cats["goals"]):
        add("Influence", drv, goal, "+")

    # WorkPackage -> its own Goal: same underlying driver ("Implement: X" -> "Achieve: X").
    for wp, goal in zip(cats["work_packages"], cats["goals"]):
        add("Realization", wp, goal, "realizes")

    # Assessment -> its own Requirement: same underlying pain point.
    for assess, req in zip(cats["assessments"], cats["requirements"]):
        add("Influence", assess, req, "identifies the need for")

    # Primary platform Node -> every Application: it's the runtime hosting
    # every in-scope application, regardless of which one (platform_primary
    # is always appended first in build_elements, so technology[0] is it).
    technology = cats["technology"]
    if technology:
        platform = technology[0]
        for app in cats["applications"]:
            add("Serving", platform, app, "hosts")

    # Gap sits between the two Plateaus by definition; Target Plateau realizes
    # every Goal (the target architecture is what achieves the engagement's goals).
    baseline, target = cats["plateaus"]
    for gap in cats["gap"]:
        add("Association", gap, baseline, "identified from")
        add("Association", gap, target, "identified from")
    for goal in cats["goals"]:
        add("Realization", target, goal, "realizes")

    return rels


def relationships_for_phase(phase_id: str, cats: dict, all_relationships: list) -> list:
    """A relationship is only declared+drawn in a phase-scoped file when both
    its endpoints are also elements of that same file - guarantees every
    generated file is self-contained and importable on its own, with no
    dangling source/target references."""
    phase_ids = {el["id"] for el in elements_for_phase(phase_id, cats)}
    return [r for r in all_relationships if r["source"] in phase_ids and r["target"] in phase_ids]


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


# ---------------------------------------------------------------------------
# Multi-view catalog (one model file gets several named views, not just one -
# mirrors the ~20-view catalog in the existing SAP reference repositories:
# a Template (legend only), several themed views, a Complete Cross-Reference)
# ---------------------------------------------------------------------------

# (key, display name, selector). Each selector pulls a themed subset out of
# `cats`; view_specs_for_scope() below intersects that subset with whatever
# elements actually exist in a given file, so a view is only added if it
# would show at least one real element there - a phase file naturally ends
# up with just the handful of themed views relevant to it, same as the
# reference repos' phase-scoped files each carrying only 3-7 of the full
# ~20-view catalog. Three reference-repo views are deliberately not attempted
# here since nothing in this generator's data model backs them honestly:
# a Current-State/Target-State split (only two placeholder Plateaus exist,
# not per-element state), and the "TOGAF ADM Cycle" wheel (a static framework
# diagram, not derived from any project data).
VIEW_SELECTORS = [
    ("architecture_vision", "Architecture Vision",
     lambda c: c["stakeholders"] + c["drivers"] + c["goals"] + c["capabilities"]),
    ("stakeholder_map", "Stakeholder Map",
     lambda c: c["stakeholders"] + c["goals"] + c["capabilities"] + c["business_processes"]),
    ("motivation_requirements", "Motivation & Requirements",
     lambda c: c["drivers"] + c["goals"] + c["principles"] + c["assessments"] + c["requirements"]),
    ("capability_map", "Capability Map",
     lambda c: c["capabilities"] + c["business_processes"]),
    ("business_architecture", "Business Architecture",
     lambda c: c["business_processes"] + c["stakeholders"][len(CORE_STAKEHOLDERS):]),
    ("business_process_value_streams", "Business Process & Value Streams",
     lambda c: c["business_processes"]),
    ("data_architecture", "Data Architecture",
     lambda c: c["data_objects"] + c["business_processes"]),
    ("application_landscape", "Application Landscape",
     lambda c: c["applications"] + [t for t in c["technology"] if t.get("tag") == "platform"]),
    ("integration_architecture", "Integration Architecture",
     lambda c: [t for t in c["technology"] if t.get("tag") == "btp"] + c["applications"]),
    ("sap_btp", "SAP BTP",
     lambda c: [t for t in c["technology"] if t.get("tag") == "btp"]),
    ("technology_architecture", "Technology Architecture",
     lambda c: c["technology"]),
    ("gap_analysis", "Gap Analysis",
     lambda c: c["requirements"] + c["plateaus"] + c["gap"]),
    ("migration_plateaus", "Migration Plateaus",
     lambda c: c["plateaus"] + c["gap"]),
    ("migration_roadmap", "Migration Roadmap",
     lambda c: c["work_packages"] + c["goals"]),
    ("work_package_overview", "Work Package Overview",
     lambda c: c["work_packages"] + c["goals"] + c["plateaus"][1:]),
    ("default_view", "Default View",
     lambda c: c["capabilities"] + c["business_processes"] + c["applications"] + c["technology"] + c["goals"]),
]


def view_specs_for_scope(scope_elements: list, cats: dict, relationships: list, complete_view_name: str) -> list:
    """Builds the multi-view catalog for one model file: a Template (legend
    only, no real elements), one themed view per VIEW_SELECTORS entry that
    yields at least one element actually present in `scope_elements`, and a
    final Complete Cross-Reference of everything in `scope_elements`."""
    scope_ids = {el["id"] for el in scope_elements}
    specs = [("template", "Template - Legend and View Information", [], [])]

    for key, view_name, selector in VIEW_SELECTORS:
        subset = [el for el in selector(cats) if el["id"] in scope_ids]
        if subset:
            specs.append((key, view_name, subset, relationships))

    specs.append(("complete", complete_view_name, scope_elements, relationships))
    return specs


def documentation_header(answers: dict, phase_title: str | None = None) -> str:
    base = f"Author: {answers.get('author', '')}; Generated: {date.today().isoformat()}. "
    base += f"{answers.get('repository_name', '')} for {answers.get('company_name', '')}, structured per the TOGAF ADM."
    if phase_title:
        base += f" Phase-scoped extract for {phase_title}."
    return base

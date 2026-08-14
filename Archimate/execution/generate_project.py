#!/usr/bin/env python3
"""
Main script: reads a questionnaire answers JSON (produced by
questionnaire.py) and generates a new project scaffold under
C:\\Archimate Repository\\<repository name>\\, structured identically to
the existing SAP Centralized IAM Repository / SAP Enterprise Repository:

  <repository name>\\Documentation\\   core + TOGAF catalog .docx deliverables
  <repository name>\\Models\\          master + per-ADM-phase ArchiMate .xml

Usage:
    python generate_project.py [path\\to\\answers.json]

If no path is given, the most recently created file in ..\\.tmp\\ is used.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

from phase_map import TOGAF_PHASES, doc_filename, model_filename
from docx_builder import build_doc
import xml_builder as xb

REPO_ROOT = Path(r"C:\Archimate Repository")
TMP_DIR = Path(__file__).parent.parent / ".tmp"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return s.strip("-")


def latest_tmp_file() -> Path:
    files = sorted(TMP_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise SystemExit(f"No answers file given and none found in {TMP_DIR}. Run questionnaire.py first.")
    return files[-1]


def documentation_index_text(scope_title: str, filenames: list | None, docs_by_phase: dict | None = None) -> str:
    """Builds the "DOCUMENTATION INDEX" text block: either a single-phase
    checklist (pass `filenames`) or the full all-phases index (pass
    `docs_by_phase`, phase title -> filenames), matching the format already
    used by hand in the SAP Enterprise Repository (its `docindex_master`
    element)."""
    lines = [f"DOCUMENTATION INDEX ({scope_title})", f"Generated: {date.today().isoformat()}", ""]
    if docs_by_phase is not None:
        for phase_title, fnames in docs_by_phase.items():
            lines.append(f"{phase_title}:")
            for fname in fnames:
                lines.append(f"  ✓ {fname}")
            lines.append("")
    else:
        for fname in (filenames or []):
            lines.append(f"  ✓ {fname}")
    return "\n".join(lines).rstrip()


def main():
    answers_path = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_tmp_file()
    answers = json.loads(answers_path.read_text(encoding="utf-8"))

    repository_name = answers["repository_name"]
    short_code = answers["short_code"]
    slug = repository_name.replace(" ", "_")
    id_slug = slugify(repository_name)

    project_dir = REPO_ROOT / repository_name
    docs_dir = project_dir / "Documentation"
    models_dir = project_dir / "Models"
    docs_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    reg = xb.Registry()
    cats = xb.build_elements(reg, answers)
    all_rels = xb.build_relationships(reg, cats)

    created_docs = []
    created_models = []
    docs_by_phase = {}  # phase title -> [filenames], for the documentation index

    for phase in TOGAF_PHASES:
        phase_docs = []
        for kind, key, title in phase["docs"]:
            fname = doc_filename(kind, key, short_code)
            path = docs_dir / fname
            build_doc(path, key, title, phase["title"], answers, short_code)
            created_docs.append(fname)
            phase_docs.append(fname)
        docs_by_phase[phase["title"]] = phase_docs

        if phase["id"] == "C":
            for suffix, phase_xid in zip(phase["model_suffixes"], ["C-data", "C-app"]):
                fname = model_filename(slug, suffix)
                els = xb.elements_for_phase(phase_xid, cats)
                rels = xb.relationships_for_phase(phase_xid, cats, all_rels)
                docindex_text = documentation_index_text(phase["title"], phase_docs)
                docindex_el = xb.build_docindex_element(docindex_text)
                els_with_index = els + [docindex_el]
                view_specs = xb.view_specs_for_scope(els_with_index, cats, rels, "Complete Phase Cross-Reference (All Elements)", docindex_element=docindex_el)
                doc_text = xb.documentation_header(answers, phase["title"])
                xml = xb.build_model_xml(f"{id_slug}-{suffix.lower()}", f"{repository_name} - {phase['title']}", doc_text, els_with_index, relationships=rels, view_specs=view_specs, phase_label=phase["title"])
                (models_dir / fname).write_text(xml, encoding="utf-8")
                created_models.append(fname)
        else:
            fname = model_filename(slug, phase["model_suffix"])
            els = xb.elements_for_phase(phase["id"], cats)
            rels = xb.relationships_for_phase(phase["id"], cats, all_rels)
            docindex_text = documentation_index_text(phase["title"], phase_docs)
            docindex_el = xb.build_docindex_element(docindex_text)
            els_with_index = els + [docindex_el]
            view_specs = xb.view_specs_for_scope(els_with_index, cats, rels, "Complete Phase Cross-Reference (All Elements)", docindex_element=docindex_el)
            doc_text = xb.documentation_header(answers, phase["title"])
            xml = xb.build_model_xml(f"{id_slug}-{phase['id'].lower()}", f"{repository_name} - {phase['title']}", doc_text, els_with_index, relationships=rels, view_specs=view_specs, phase_label=phase["title"])
            (models_dir / fname).write_text(xml, encoding="utf-8")
            created_models.append(fname)

    # Master model = union of every element (and relationship) used across phases
    master_fname = model_filename(slug, None)
    master_els = xb.master_elements(cats)
    master_docindex_text = documentation_index_text("All Phases", None, docs_by_phase)
    master_docindex_el = xb.build_docindex_element(master_docindex_text)
    master_els_with_index = master_els + [master_docindex_el]
    master_view_specs = xb.view_specs_for_scope(master_els_with_index, cats, all_rels, "Complete Model Cross-Reference (All Elements)", docindex_element=master_docindex_el)
    master_doc = xb.documentation_header(answers)
    master_xml = xb.build_model_xml(id_slug, repository_name, master_doc, master_els_with_index, relationships=all_rels, view_specs=master_view_specs, phase_label="Master Model (all phases)")
    (models_dir / master_fname).write_text(master_xml, encoding="utf-8")
    created_models.append(master_fname)

    print(f"Created project: {project_dir}")
    print(f"  Documentation/ : {len(created_docs)} files")
    print(f"  Models/        : {len(created_models)} files")
    print("Open the Models\\ files in Archi, and the Documentation\\ files in Word to continue elaborating each ADM phase.")


if __name__ == "__main__":
    main()

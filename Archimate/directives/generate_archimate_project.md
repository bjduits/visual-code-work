# Generate a TOGAF/ArchiMate Project Scaffold

## Goal
Stand up a new TOGAF ADM-structured project under `C:\Archimate Repository\<repository name>\`, matching the structure of the two existing repositories there (SAP Centralized IAM Repository, SAP Enterprise Repository): a `Documentation\` folder of TOGAF deliverables and a `Models\` folder of ArchiMate models, one per ADM phase plus a master model.

## Inputs
- Repository / project name (becomes the folder name under `C:\Archimate Repository`)
- Short code / abbreviation (2-6 letters, used in catalog document filenames, e.g. `ENT`, `IAM`)
- Company / engagement basics: engagement type, industry, company size, geographic scope
- Current situation: current ERP/core system landscape, current pain points
- Motivation: strategic drivers, architecture principles
- Business processes in scope (SAP E2E process catalog)
- Applications in scope (SAP product catalog)
- Platform: primary hosting/delivery model, supporting SAP BTP services, hyperscaler preference

All inputs are collected as multiple-choice/free-text via `execution/questionnaire.py` - no need to gather them manually.

## Tools/Scripts
- `execution/questionnaire.py` - interactive CLI intake, writes answers to `../.tmp/<slug>_<timestamp>.json`
- `execution/generate_project.py` - reads an answers JSON and writes the full project scaffold to `C:\Archimate Repository\<repository name>\`
- `execution/phase_map.py` - single source of truth for the TOGAF ADM phase -> document/model mapping (edit here to add/remove deliverables)
- `execution/catalogs.py` - the multiple-choice option lists (SAP-product-centric first cut; extend here for other vendor stacks)
- `execution/docx_builder.py` / `execution/xml_builder.py` - deliverable generators, not run directly

Requires `python-docx` (`pip install python-docx`).

## Process
1. Run `python execution/questionnaire.py` and answer the prompts.
2. Note the answers file path it prints (also the newest file in `.tmp/`).
3. Run `python execution/generate_project.py` (auto-picks the newest `.tmp/*.json`) or pass the path explicitly.
4. Open `Models\*.xml` in Archi and `Documentation\*.docx` in Word to elaborate each phase with the working team.

## Outputs
- `C:\Archimate Repository\<repository name>\Documentation\` - 8 core numbered docs (`01_Architecture_Vision.docx` ... `08_Architecture_Roadmap.docx`) + `TOGAF_Catalog_<CODE>_*.docx` catalog artifacts per phase
- `C:\Archimate Repository\<repository name>\Models\` - master `<slug>.xml` + one ArchiMate model per ADM phase (Preliminary, A-H; Phase C produces both a Data and an Application model)
- Intermediate answers JSON in `.tmp/` (never commit, always regenerable)

### TOGAF ADM phase -> deliverable map
| Phase | Documentation | Models |
|---|---|---|
| Preliminary | Request for Architecture Work, Organizational Model for EA, Tailored Architecture Framework, Architecture Repository, Business Principles/Goals/Drivers | `..._Preliminary_Phase.xml` |
| A - Architecture Vision | `01_Architecture_Vision`, Statement of Architecture Work, Capability Assessment, Communications Plan, Architecture Definition Document (draft) | `..._Phase_A_-_Architecture_Vision.xml` |
| B - Business Architecture | `02_Business_Architecture` | `..._Phase_B_-_Business_Architecture.xml` |
| C - Information Systems Architectures | `03_Data_Architecture`, `04_Application_Architecture`, Architecture Deliverables C&D | `..._Phase_C_-_Data_Architecture.xml`, `..._Phase_C_-_Application_Architecture.xml` |
| D - Technology Architecture | `05_Technology_Architecture` | `..._Phase_D_-_Technology_Architecture.xml` |
| E - Opportunities and Solutions | `06_Architecture_Requirements_Specification`, Architecture Building Blocks, Solution Building Blocks | `..._Phase_E_-_Opportunities_and_Solutions.xml` |
| F - Migration Planning | `07_Implementation_and_Migration_Plan`, Architecture Contract | `..._Phase_F_-_Migration_Planning.xml` |
| G - Implementation Governance | `08_Architecture_Roadmap`, Implementation Governance Model, Compliance Assessment | `..._Phase_G_-_Implementation_Governance.xml` |
| H - Architecture Change Management | Requirements Impact Assessment, Change Request | `..._Phase_H_-_Architecture_Change_Management.xml` |
| (all phases) | - | master `<repository>.xml` = union of every element used across phases |

Core numbered docs (`01`-`08`) are unprefixed, matching the SAP Enterprise Repository convention. Catalog docs are named `TOGAF_Catalog_<SHORT_CODE>_<Phase>_<Artifact>.docx`. Element identifiers are assigned once per conceptual element and reused across every model file that references it, so phase models stay cross-referenceable against the master model.

## Edge Cases
- **Re-running for the same repository name**: `generate_project.py` overwrites the generated skeleton files. Only safe before real content has been added to the docs/models - do this before elaboration starts, not after.
- **No answers file found**: run `questionnaire.py` first; `generate_project.py` errors out with a clear message if `.tmp/` has no JSON files and none was passed explicitly.
- **Non-SAP engagement**: `catalogs.py` is SAP-first by design. Add new option lists there and branch `xml_builder.build_elements` / `docx_builder.DOC_SCOPE_FIELDS` as needed - `phase_map.py` and the generation flow don't need to change.

## Notes
- Questionnaire answers drive content mainly for Phases Preliminary-D (vision, business, data/application, technology), since that's what the intake actually asks about. Phases E-H get lighter, mostly generic skeletons (work packages per driver, baseline/target plateaus, a gap placeholder, change-request log) - elaborate these by hand once earlier phases are validated with stakeholders.
- Capability maturity is generated as `"To be assessed"` rather than a fabricated value - fill in real ratings after a current-state workshop.
- No `<relationships>` are generated between elements yet, only elements - keeps the skeleton valid and simple to review; add relationships in Archi once elements are confirmed.
- Deliverables land in `C:\Archimate Repository\`, outside this repo - that folder is the actual architecture repository the team works from, not something to commit here.

## Walkthrough

A plain-language run-through of what happens when you actually do this, start to finish.

**Before you start:** have `python-docx` installed (`pip install python-docx`) and know roughly what the engagement is about - company, industry, current pain points. You don't need exact answers, just a first pass; everything here is a refinable draft.

1. **Open a terminal in `Archimate/execution/` and run `python questionnaire.py`.**
   You'll see a friendly numbered questionnaire, one section at a time - repository basics, then business plan, current situation, motivation, business processes, applications, and platform. Multiple-choice questions show a numbered list; type one number, or several separated by commas (or `all`). Free-text questions (repository name, company name, author) just take what you type.

2. **Answer through to the end.**
   The last question is your hyperscaler preference. Right after that, you'll see a summary line: `Answers saved to: ...\.tmp\<slug>_<timestamp>.json` followed by the exact next command to run.

3. **Run `python generate_project.py`.**
   No arguments needed - it automatically picks up the answers file you just created. Within a couple of seconds you'll see:
   ```
   Created project: C:\Archimate Repository\<your repository name>
     Documentation/ : 25 files
     Models/        : 11 files
   ```

4. **Open the new folder at `C:\Archimate Repository\<your repository name>\`.**
   You'll find it structured exactly like the two existing repositories: a `Documentation\` folder with 25 `.docx` files (8 core numbered deliverables plus TOGAF catalog artifacts) and a `Models\` folder with 11 `.xml` files (one master plus one per ADM phase).

5. **Open a `Documentation\*.docx` file, e.g. `01_Architecture_Vision.docx`, in Word.**
   You'll see a title page with your repository/company/author, a Purpose section explaining what this deliverable is for, a Scope section already filled in with the relevant answers you gave (e.g. industry, drivers, business processes - whichever apply to that document), a Content placeholder to replace during the real workshop, and a "DRAFT" status line.

6. **Open a `Models\*.xml` file, e.g. `..._Phase_A_-_Architecture_Vision.xml`, in Archi.**
   You'll see it import cleanly and show real elements: your chosen stakeholders, drivers, goals, and capabilities (one Capability per business process you picked), not empty placeholders.

**You're done when:** every phase folder has content pulled straight from your answers, the master model in `Models\` (no phase suffix) shows the union of everything across every phase, and you've got a working starting point to walk into the first ADM workshop with instead of a blank page.

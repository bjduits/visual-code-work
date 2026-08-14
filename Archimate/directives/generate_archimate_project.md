# Generate a TOGAF/ArchiMate Project Scaffold

## Goal
Stand up a new TOGAF ADM-structured project under `C:\Archimate Repository\<repository name>\`, matching the structure of the two existing repositories there (SAP Centralized IAM Repository, SAP Enterprise Repository): a `Documentation\` folder of TOGAF deliverables and a `Models\` folder of ArchiMate models, one per ADM phase plus a master model.

Also keeps local, editable copies of every project (new or pre-existing) under `../projects/` so they can be viewed, finetuned, and validated from inside VS Code, with scripts to sync changes back out to `C:\Archimate Repository\` - the canonical location Archi and Word open directly.

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
- `execution/sync_from_repository.py [project name]` - pulls project folder(s) from `C:\Archimate Repository\` into `../projects/<name>\`; no argument = every project, auto-discovered (so a brand-new one generated later is picked up automatically)
- `execution/sync_to_repository.py <project name> | --all [--no-backup]` - pushes local edits in `../projects/<name>\` back out to `C:\Archimate Repository\<name>\`, first zipping whatever's currently there into `C:\Archimate Repository\.backups\<name>\` (keeps the 5 most recent per project) so a bad push can be recovered from
- `execution/validate_models.py [project name] [--fix]` - checks every `Models\*.xml` under `../projects/` for malformed XML, duplicate identifiers, elements missing a name, unrecognized `xsi:type`, dangling relationship source/target references, and properties referencing an undeclared `propertyDefinitionRef`. `--fix` auto-repairs the last of those (adds the missing `propertyDefinitions` entry)

Requires `python-docx` (`pip install python-docx`).

## Process
1. Run `python execution/questionnaire.py` and answer the prompts.
2. Note the answers file path it prints (also the newest file in `.tmp/`).
3. Run `python execution/generate_project.py` (auto-picks the newest `.tmp/*.json`) or pass the path explicitly.
4. Run `python execution/sync_from_repository.py` to pull the new (and every other) project into `../projects/` for local editing.
5. Open `../projects/<name>/Models\*.xml` in Archi and `../projects/<name>/Documentation\*.docx` in Word, or ask Claude to adjust/finetune them directly, or extend `validate_models.py` with new checks.
6. Run `python execution/validate_models.py` (optionally `--fix`) before pushing changes back out.
7. Run `python execution/sync_to_repository.py <name>` to push the finetuned files back to `C:\Archimate Repository\<name>\`.

## Outputs
- `C:\Archimate Repository\<repository name>\Documentation\` - 8 core numbered docs (`01_Architecture_Vision.docx` ... `08_Architecture_Roadmap.docx`) + 20 `TOGAF_Catalog_<CODE>_*.docx` catalog artifacts per phase = 28 total
- `C:\Archimate Repository\<repository name>\Models\` - master `<slug>.xml` + one ArchiMate model per ADM phase (Preliminary, A-H; Phase C produces both a Data and an Application model) = 11 total
- `../projects/<repository name>\` - a local working copy of the above (Documentation + Models), tracked in this repo, kept in sync via `sync_from_repository.py` / `sync_to_repository.py`
- Intermediate answers JSON in `.tmp/` (never commit, always regenerable)
- **A finished cycle (every phase through H) produces 39 artifacts total**: 28 Documentation files + 11 Models files. That's the answer once and for all - it won't drift as long as this table and `phase_map.py` stay in sync.

### TOGAF ADM phase -> deliverable map
| Phase | Documentation | Models |
|---|---|---|
| Preliminary | Request for Architecture Work, Organizational Model for EA, Tailored Architecture Framework, Architecture Repository, Business Principles/Goals/Drivers, **Architecture Principles** | `..._Preliminary_Phase.xml` |
| A - Architecture Vision | `01_Architecture_Vision`, Statement of Architecture Work, Capability Assessment, Communications Plan, Architecture Definition Document (draft) | `..._Phase_A_-_Architecture_Vision.xml` |
| B - Business Architecture | `02_Business_Architecture` | `..._Phase_B_-_Business_Architecture.xml` |
| C - Information Systems Architectures | `03_Data_Architecture`, `04_Application_Architecture`, Architecture Deliverables C&D | `..._Phase_C_-_Data_Architecture.xml`, `..._Phase_C_-_Application_Architecture.xml` |
| D - Technology Architecture | `05_Technology_Architecture` | `..._Phase_D_-_Technology_Architecture.xml` |
| E - Opportunities and Solutions | `06_Architecture_Requirements_Specification`, Architecture Building Blocks, Solution Building Blocks, **Opportunities & Solutions Assessment**, **Architecture Definition Document (formal)** | `..._Phase_E_-_Opportunities_and_Solutions.xml` |
| F - Migration Planning | `07_Implementation_and_Migration_Plan`, Architecture Contract | `..._Phase_F_-_Migration_Planning.xml` |
| G - Implementation Governance | `08_Architecture_Roadmap`, Implementation Governance Model, Compliance Assessment Report | `..._Phase_G_-_Implementation_Governance.xml` |
| H - Architecture Change Management | Requirements Impact Assessment, Change Request | `..._Phase_H_-_Architecture_Change_Management.xml` |
| (all phases) | - | master `<repository>.xml` = union of every element used across phases |

The Architecture Definition Document deliberately appears twice, by design: a Phase A **draft** (early sketch, right after Architecture Vision) and a Phase E **formal** version (baselined once Business/Data/Application/Technology architectures from Phases B-D are settled) - standard TOGAF practice of progressively elaborating the ADD rather than writing it once.

Core numbered docs (`01`-`08`) are unprefixed, matching the SAP Enterprise Repository convention. Catalog docs are named `TOGAF_Catalog_<SHORT_CODE>_<Phase>_<Artifact>.docx`. Element identifiers are assigned once per conceptual element and reused across every model file that references it, so phase models stay cross-referenceable against the master model.

## Edge Cases
- **Re-running for the same repository name**: `generate_project.py` overwrites the generated skeleton files. Only safe before real content has been added to the docs/models - do this before elaboration starts, not after.
- **No answers file found**: run `questionnaire.py` first; `generate_project.py` errors out with a clear message if `.tmp/` has no JSON files and none was passed explicitly.
- **Non-SAP engagement**: `catalogs.py` is SAP-first by design. Add new option lists there and branch `xml_builder.build_elements` / `docx_builder.DOC_SCOPE_FIELDS` as needed - `phase_map.py` and the generation flow don't need to change.
- **`sync_from_repository.py` / `sync_to_repository.py` overwrite the destination.** Both are one-way, last-write-wins copies (`shutil.copytree(..., dirs_exist_ok=True)`) - no merge, no diffing. If both `C:\Archimate Repository\<name>\` and `../projects/<name>\` have been edited independently since the last sync, one side's changes will be silently overwritten. Run `validate_models.py` and eyeball what changed before pushing. As a safety net, `sync_to_repository.py` zips whatever currently sits at `C:\Archimate Repository\<name>\` into `C:\Archimate Repository\.backups\<name>\<name>_<timestamp>.zip` before every push, keeping the 5 most recent (pass `--no-backup` to skip). To recover: unzip the desired backup back over `C:\Archimate Repository\<name>\`, or into `../projects/<name>\` if you want to review/edit it locally first.
- **Relationship source/target warnings on phase-scoped files are often expected, not bugs, for relationships added by hand in Archi afterward**: a phase model is intentionally a subset of the master model's elements, so a manually-added relationship whose other end lives in a different phase will warn here. Only treat it as a real problem if the referenced id doesn't exist anywhere (check the master `<slug>.xml`). This doesn't apply to the auto-generated relationships from `build_relationships` - those are pre-filtered per phase (see Notes) so they never trigger this warning in the first place.

## Notes
- Questionnaire answers drive content mainly for Phases Preliminary-D (vision, business, data/application, technology), since that's what the intake actually asks about. Phases E-H get lighter, mostly generic skeletons (work packages per driver, baseline/target plateaus, a gap placeholder, change-request log) - elaborate these by hand once earlier phases are validated with stakeholders.
- Capability maturity is generated as `"To be assessed"` rather than a fabricated value - fill in real ratings after a current-state workshop.
- `xml_builder.build_relationships` derives a default `<relationships>` set purely from correspondences that already exist in the data - same underlying answer, same list position (e.g. Capability↔BusinessProcess, Driver↔Goal, "Business Process Owner - X" stakeholder↔Capability/BusinessProcess X). It never links elements whose correspondence isn't actually implied by the questionnaire - e.g. specific applications are never wired to specific capabilities, since those two lists come from unrelated questions and guessing a pairing would assert business logic that isn't real. `relationships_for_phase` only keeps a relationship in a phase-scoped file when both endpoints are also elements of that file, so every generated file stays self-contained and import-clean with no dangling references; the master model gets the full set. Add anything richer by hand in Archi.
- Every model file gets a multi-view catalog (`xml_builder.view_specs_for_scope` + `build_views_xml`), not just one diagram - mirrors the ~20-view catalog in the SAP reference repos: a "Template - Legend and View Information" view (legend only, no real elements) first, then one themed view per `VIEW_SELECTORS` entry (Stakeholder Map, Capability Map, Business Architecture, Data Architecture, Application Landscape, Technology Architecture, Gap Analysis, Migration Roadmap, etc.) that's only included if it would actually show at least one element present in that file, then a "Complete \[Phase|Model\] Cross-Reference (All Elements)" view last. A phase-scoped file naturally ends up with just the handful of themed views relevant to its own content. Three reference-repo views are deliberately not attempted since nothing in the generator's data model backs them honestly: a Current-State/Target-State split (only two placeholder Plateaus exist, not per-element state) and the "TOGAF ADM Cycle" wheel (a static framework diagram, not derived from project data).
- Every view is laid out the same way (`xml_builder._layout_elements`): elements placed in layout columns (`LAYER_ORDER`), colored per their true ArchiMate layer via `LAYER_TO_CANONICAL` (some layers are deliberately split across more than one layout column - e.g. Motivation into "cause" Driver/Assessment/Principle and "effect" Goal/Requirement columns, Stakeholders its own column, Gap its own column ahead of the rest of Implementation & Migration - so that elements `build_relationships` actually connects land in *adjacent* columns instead of an unrelated column sitting between them and the connector cutting across it). From the second column onward, each element is also positioned near the average y of its already-placed related neighbors (a single left-to-right barycenter pass) rather than just stacked in list order, keeping connected elements level with each other. This isn't perfect for every relationship in the densest view (the master model's "Complete Model Cross-Reference", where e.g. Stakeholder-owns->BusinessProcess still crosses the Capability column, since Stakeholder/Capability/BusinessProcess form a triangle no single left-to-right column order can fully untangle) but resolves it for every themed view, where the full triangle never co-occurs. The LEGEND (title + one swatch per layer) is declared once per file and reused (via a fresh `<node>`) across every view in it, matching how the SAP reference repos share their legend across ~20 views instead of duplicating it; a fresh VIEW INFORMATION metadata box is added per view.
- Deliverables land in `C:\Archimate Repository\`, outside this repo - that folder is the actual architecture repository the team works from, not something to commit here. `../projects/` is the git-tracked mirror used for local editing.
- `xml_builder.build_model_xml` auto-derives the `<propertyDefinitions>` block from whatever `propertyDefinitionRef`s the passed elements actually use (see `_property_defs_xml`) - this was added after `validate_models.py` caught generated files referencing `propdef-maturity` without ever declaring it. Any future element property added to `xml_builder.build_elements` gets its definition generated automatically; no separate bookkeeping needed.

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
   You'll see it import cleanly and show real elements: your chosen stakeholders, drivers, goals, and capabilities (one Capability per business process you picked), not empty placeholders. In the Views folder you'll find several named diagrams already laid out, not one blank canvas - a Template (legend only), themed views relevant to that file's content (e.g. "Stakeholder Map", "Architecture Vision", "Capability Map" for a Phase A file), and a Complete Cross-Reference of everything in it - elements arranged in columns by ArchiMate layer, with connecting lines already drawn wherever a relationship exists (e.g. each Business Process Owner stakeholder linked to their capability).

**You're done when:** every phase folder has content pulled straight from your answers, the master model in `Models\` (no phase suffix) shows the union of everything across every phase, and you've got a working starting point to walk into the first ADM workshop with instead of a blank page.

## Walkthrough: sync and validate an existing project

A plain-language run-through of pulling a project into VS Code, fixing it up, and pushing it back.

**Before you start:** know which project you're working on - either one already sitting in `C:\Archimate Repository\` (e.g. `SAP Enterprise Repository`) or one you just generated.

1. **Run `python execution/sync_from_repository.py`.**
   With no project name, it walks every folder under `C:\Archimate Repository\` and copies each one into `../projects/<name>\`. You'll see one `OK` line per project with a file count, e.g. `OK    SAP Enterprise Repository  (Documentation: 28 files, Models: 11 files)`.

2. **Open `../projects/` in the VS Code file tree.**
   You'll see each repository as its own folder, `Documentation\` and `Models\` inside, exactly as they appear at the canonical location - except now they're regular files in this workspace, so you can open, edit, or ask Claude to adjust them directly.

3. **Run `python execution/validate_models.py`.**
   Every project's `Models\*.xml` gets checked in turn. You'll see a per-file `[OK]`, `[WARN]`, or `[ERROR]` line, with the specific problem spelled out underneath any that aren't clean - e.g. `element 'cap1' property references undeclared propertyDefinitionRef 'propdef-maturity'`. A summary line at the end totals the errors and warnings found.

4. **If there are errors, run `python execution/validate_models.py --fix`.**
   Whatever's safely auto-fixable gets repaired in place (currently: adding a missing `propertyDefinitions` entry for a property that's referenced but never declared). Re-run without `--fix` afterward to confirm everything now shows `[OK]`.

5. **For anything not auto-fixable, ask Claude to fix it directly**, or make the edit yourself in the `.xml`/`.docx` file - the validator tells you exactly which element/relationship and file to look at.

6. **Run `python execution/sync_to_repository.py "<project name>"`** (or `--all` for everything) once you're happy with the result.
   You'll see `OK    <name>  ... -> C:\Archimate Repository\<name>`, confirming the finetuned files have overwritten the canonical copy that Archi and Word open.

**You're done when:** `validate_models.py` shows `0 error(s), 0 warning(s)` for the project you touched, and `sync_to_repository.py` has pushed the result back to `C:\Archimate Repository\`.

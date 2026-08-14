#!/usr/bin/env python3
"""
Interactive intake questionnaire for a new TOGAF/ArchiMate project.
Multiple-choice first, SAP-product-centric. Saves answers as JSON into
../.tmp/ (intermediate, regenerable - never commit), ready for
generate_project.py to turn into a full project scaffold under
C:\\Archimate Repository\\<repository name>\\.

Usage:
    python questionnaire.py
"""

import getpass
import json
from datetime import datetime
from pathlib import Path

import catalogs as cat

TMP_DIR = Path(__file__).parent.parent / ".tmp"


def ask_text(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{prompt}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        print("  Please enter a value.")


def ask_single(prompt: str, options: list) -> str:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input("Choose one [1-{}]: ".format(len(options))).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("  Invalid choice, try again.")


def ask_multi(prompt: str, options: list) -> list:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print("  (comma-separated numbers, e.g. 1,3,5 - or 'all')")
    while True:
        raw = input("Choose one or more: ").strip().lower()
        if raw == "all":
            return list(options)
        if not raw:
            print("  Please select at least one option (or 'all').")
            continue
        try:
            idxs = [int(x.strip()) for x in raw.split(",") if x.strip()]
            if all(1 <= i <= len(options) for i in idxs):
                # de-dupe, preserve selection order
                seen = []
                for i in idxs:
                    val = options[i - 1]
                    if val not in seen:
                        seen.append(val)
                return seen
        except ValueError:
            pass
        print("  Invalid selection, try again.")


def main():
    print("=" * 70)
    print("TOGAF / ArchiMate project intake questionnaire")
    print("=" * 70)

    answers = {}

    print("\n-- Repository basics --")
    answers["repository_name"] = ask_text(
        "Repository / project name (becomes the folder name under C:\\Archimate Repository)"
    )
    answers["short_code"] = ask_text(
        "Short code / abbreviation (2-6 letters, used in catalog document filenames, e.g. ENT, IAM)"
    ).upper()
    answers["author"] = ask_text("Author / architect name", default=getpass.getuser())
    answers["company_name"] = ask_text("Company / enterprise name")

    print("\n-- New company / business plan --")
    answers["engagement_type"] = ask_single("Engagement type", cat.ENGAGEMENT_TYPES)
    answers["industry"] = ask_single("Industry sector", cat.INDUSTRIES)
    answers["company_size"] = ask_single("Company size", cat.COMPANY_SIZES)
    answers["geo_scope"] = ask_single("Geographic scope", cat.GEO_SCOPES)

    print("\n-- Current situation --")
    answers["current_erp"] = ask_multi(
        "Current ERP / core system landscape (select all that apply)", cat.CURRENT_ERP_LANDSCAPE
    )
    answers["pain_points"] = ask_multi(
        "Current issues / pain points (select all that apply)", cat.PAIN_POINTS
    )

    print("\n-- Motivation --")
    answers["drivers"] = ask_multi(
        "Strategic drivers (select all that apply)", cat.DRIVERS
    )
    answers["principles"] = ask_multi(
        "Architecture principles to adopt (select all that apply)", cat.PRINCIPLES
    )

    print("\n-- Propose business processes --")
    answers["business_processes"] = ask_multi(
        "Business processes in scope (select all that apply)", cat.BUSINESS_PROCESSES
    )

    print("\n-- Propose applications (SAP product catalog) --")
    answers["applications"] = ask_multi(
        "Applications in scope (select all that apply)", cat.SAP_APPLICATIONS
    )

    print("\n-- Propose platform --")
    answers["platform_primary"] = ask_single(
        "Primary hosting / delivery model", cat.PLATFORM_PRIMARY
    )
    answers["btp_services"] = ask_multi(
        "Supporting SAP BTP services (select all that apply)", cat.BTP_SERVICES
    )
    answers["hyperscaler"] = ask_single(
        "Hyperscaler preference", cat.HYPERSCALERS
    )

    TMP_DIR.mkdir(exist_ok=True)
    slug = "".join(c if c.isalnum() else "_" for c in answers["repository_name"]).strip("_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = TMP_DIR / f"{slug}_{ts}.json"
    out_path.write_text(json.dumps(answers, indent=2), encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"Answers saved to: {out_path}")
    print(f"Next step: python generate_project.py \"{out_path}\"")
    print("=" * 70)


if __name__ == "__main__":
    main()

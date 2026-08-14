#!/usr/bin/env python3
"""
Pulls every project folder from C:\\Archimate Repository\\ into
../projects/<project name>\\ so it can be viewed, edited, and validated
from inside VS Code. Auto-discovers projects - run this after generating a
new project (generate_project.py) or after edits made directly in Archi/Word,
to refresh the local working copy.

C:\\Archimate Repository\\ remains the source of truth; this only ever reads
from it. Use sync_to_repository.py to push local edits back out.

Usage:
    python sync_from_repository.py [project name]

If no project name is given, every project folder under C:\\Archimate
Repository\\ is synced.
"""

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\Archimate Repository")
LOCAL_PROJECTS_DIR = Path(__file__).parent.parent / "projects"


def sync_project(name: str) -> tuple[int, int]:
    src = REPO_ROOT / name
    dst = LOCAL_PROJECTS_DIR / name
    docs_count = len(list((src / "Documentation").glob("*"))) if (src / "Documentation").is_dir() else 0
    models_count = len(list((src / "Models").glob("*"))) if (src / "Models").is_dir() else 0
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return docs_count, models_count


def main():
    if not REPO_ROOT.is_dir():
        raise SystemExit(f"{REPO_ROOT} not found.")

    if len(sys.argv) > 1:
        names = [sys.argv[1]]
    else:
        names = sorted(p.name for p in REPO_ROOT.iterdir() if p.is_dir())

    if not names:
        print(f"No project folders found under {REPO_ROOT}.")
        return

    LOCAL_PROJECTS_DIR.mkdir(exist_ok=True)
    for name in names:
        src = REPO_ROOT / name
        if not src.is_dir():
            print(f"SKIP  {name} - not found under {REPO_ROOT}")
            continue
        docs_count, models_count = sync_project(name)
        print(f"OK    {name}  (Documentation: {docs_count} files, Models: {models_count} files)")

    print(f"\nSynced into {LOCAL_PROJECTS_DIR}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Pushes a project folder from ../projects/<project name>\\ back out to
C:\\Archimate Repository\\<project name>\\ - the canonical location that
Archi and Word open directly. Run this after finetuning a model or document
locally in VS Code.

Refuses to run with unstaged/uncommitted local edits unresolved is NOT
enforced here (this repo's .tmp/git conventions are separate) - it simply
overwrites the destination files. Run validate_models.py first if you want
a sanity check before pushing.

Usage:
    python sync_to_repository.py <project name>
    python sync_to_repository.py --all
"""

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\Archimate Repository")
LOCAL_PROJECTS_DIR = Path(__file__).parent.parent / "projects"


def push_project(name: str) -> tuple[int, int]:
    src = LOCAL_PROJECTS_DIR / name
    dst = REPO_ROOT / name
    docs_count = len(list((src / "Documentation").glob("*"))) if (src / "Documentation").is_dir() else 0
    models_count = len(list((src / "Models").glob("*"))) if (src / "Models").is_dir() else 0
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return docs_count, models_count


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)

    if sys.argv[1] == "--all":
        names = sorted(p.name for p in LOCAL_PROJECTS_DIR.iterdir() if p.is_dir())
    else:
        names = [sys.argv[1]]

    for name in names:
        src = LOCAL_PROJECTS_DIR / name
        if not src.is_dir():
            print(f"SKIP  {name} - not found under {LOCAL_PROJECTS_DIR}")
            continue
        docs_count, models_count = push_project(name)
        print(f"OK    {name}  (Documentation: {docs_count} files, Models: {models_count} files) -> {REPO_ROOT / name}")


if __name__ == "__main__":
    main()

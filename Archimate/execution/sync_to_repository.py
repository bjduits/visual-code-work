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

Before overwriting, whatever currently sits at the destination is zipped into
C:\\Archimate Repository\\.backups\\<project name>\\ (timestamped), keeping
only the MAX_BACKUPS most recent zips per project - a quick way to recover
if a push turns out to have clobbered something (see the sync overwrite
Edge Case in generate_archimate_project.md). Pass --no-backup to skip this.

Usage:
    python sync_to_repository.py <project name> [--no-backup]
    python sync_to_repository.py --all [--no-backup]
"""

import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(r"C:\Archimate Repository")
LOCAL_PROJECTS_DIR = Path(__file__).parent.parent / "projects"
BACKUPS_DIR = REPO_ROOT / ".backups"
MAX_BACKUPS = 5


def backup_project(name: str) -> Path | None:
    """Zips the current C:\\Archimate Repository\\<name>\\ into
    .backups\\<name>\\ before it gets overwritten, then prunes to the
    MAX_BACKUPS most recent zips for that project. Returns the new zip's
    path, or None if there was nothing at the destination yet to back up
    (first-ever push for this project)."""
    dst = REPO_ROOT / name
    if not dst.is_dir():
        return None

    project_backups_dir = BACKUPS_DIR / name
    project_backups_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = project_backups_dir / f"{name}_{timestamp}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in dst.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(dst))

    existing = sorted(project_backups_dir.glob(f"{name}_*.zip"), key=lambda p: p.stat().st_mtime)
    for old in existing[:-MAX_BACKUPS]:
        old.unlink()

    return zip_path


def push_project(name: str) -> tuple[int, int]:
    src = LOCAL_PROJECTS_DIR / name
    dst = REPO_ROOT / name
    docs_count = len(list((src / "Documentation").glob("*"))) if (src / "Documentation").is_dir() else 0
    models_count = len(list((src / "Models").glob("*"))) if (src / "Models").is_dir() else 0
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return docs_count, models_count


def main():
    args = [a for a in sys.argv[1:] if a != "--no-backup"]
    do_backup = "--no-backup" not in sys.argv[1:]

    if not args:
        raise SystemExit(__doc__)

    if args[0] == "--all":
        names = sorted(p.name for p in LOCAL_PROJECTS_DIR.iterdir() if p.is_dir())
    else:
        names = [args[0]]

    for name in names:
        src = LOCAL_PROJECTS_DIR / name
        if not src.is_dir():
            print(f"SKIP  {name} - not found under {LOCAL_PROJECTS_DIR}")
            continue

        backup_note = ""
        if do_backup:
            zip_path = backup_project(name)
            if zip_path:
                backup_note = f"  [backup: {zip_path.relative_to(REPO_ROOT)}]"

        docs_count, models_count = push_project(name)
        print(f"OK    {name}  (Documentation: {docs_count} files, Models: {models_count} files) -> {REPO_ROOT / name}{backup_note}")


if __name__ == "__main__":
    main()

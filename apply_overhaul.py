"""
Drop-in installer for the Obsidian UI overhaul + demo suite.

Usage (from anywhere):   python apply_overhaul.py /path/to/ai_recruitment_system
It backs up every file it replaces into <project>/_backup_before_overhaul/ and then copies the new/changed files from
the 'overlay' folder next to this script. Re-running is safe. To undo: copy the backup folder's contents back.
"""
import os
import shutil
import sys

here = os.path.dirname(os.path.abspath(__file__))
overlay = os.path.join(here, "overlay")
target = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
if not os.path.isfile(os.path.join(target, "app.py")):
    sys.exit(f"'{target}' does not look like the project root (app.py not found).")
backup = os.path.join(target, "_backup_before_overhaul")
n_new = n_rep = 0
for root, _, files in os.walk(overlay):
    for name in files:
        src = os.path.join(root, name)
        rel = os.path.relpath(src, overlay)
        dst = os.path.join(target, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            bk = os.path.join(backup, rel)
            if not os.path.exists(bk):
                os.makedirs(os.path.dirname(bk), exist_ok=True)
                shutil.copy2(dst, bk)
            n_rep += 1
        else:
            n_new += 1
        shutil.copy2(src, dst)
print(f"Done: {n_rep} files replaced (backed up to {backup}), {n_new} new files added.")
print("Next: python -m pytest -q   then   python run_app.py")

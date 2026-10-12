"""
Script to create a clean, lightweight ZIP file of the AI Recruitment System.
Excludes huge folders like frontend/node_modules, caches, and temp files,
reducing the ZIP from ~65MB (7,500+ files) down to ~2MB (440 files) so that:
1. Windows path length limits (MAX_PATH / Error 0x80010135) don't drop files during extraction.
2. Email/chat size limits (25MB) are not exceeded.
3. No files are lost or corrupted during transfer.
"""

import os
import sys
import zipfile
from pathlib import Path

# Directories to exclude
EXCLUDE_DIRS = {
    'node_modules',
    '__pycache__',
    '.pytest_cache',
    '_to_delete',
    '.git',
    'dist',
    'venv',
    '.venv',
    'env',
}

# Files / extensions to exclude
EXCLUDE_EXTS = {'.pyc', '.pyo', '.pyd', '.zip', '.tar', '.gz'}
EXCLUDE_FILES = {'.DS_Store', 'Thumbs.db'}

def create_zip(output_path=None):
    root_dir = Path(__file__).resolve().parent.parent
    if output_path is None:
        output_path = root_dir.parent / "ai_recruitment_system_clean.zip"
    else:
        output_path = Path(output_path)

    print(f"Creating clean zip from: {root_dir}")
    print(f"Target zip destination: {output_path}")

    count = 0
    total_uncompressed = 0

    with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(root_dir):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.git')]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in EXCLUDE_EXTS or file in EXCLUDE_FILES:
                    continue
                
                # Relative path inside zip
                rel_path = file_path.relative_to(root_dir)
                archive_name = Path("ai_recruitment_system") / rel_path
                
                zf.write(file_path, arcname=str(archive_name).replace('\\', '/'))
                count += 1
                total_uncompressed += file_path.stat().st_size

    zip_size_mb = output_path.stat().st_size / (1024 * 1024)
    raw_size_mb = total_uncompressed / (1024 * 1024)

    print("\n[SUCCESS] Clean ZIP Created Successfully!")
    print(f"- Total files included: {count}")
    print(f"- Uncompressed size:   {raw_size_mb:.2f} MB")
    print(f"- Compressed ZIP size:  {zip_size_mb:.2f} MB")
    print(f"- Saved at:             {output_path}\n")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else None
    create_zip(out)

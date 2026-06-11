#!/usr/bin/env python
"""
Script to dump all relevant Django project files into a single text file.
Useful for sharing code with AI assistants or creating a full codebase snapshot.
"""

import os
import sys
from datetime import datetime

# ---------- CONFIGURATION ----------
# Directories and file patterns to exclude
EXCLUDED_DIRS = {
    '__pycache__', 'migrations', 'venv', 'env', '.venv', '.env',
    'static', 'media', 'node_modules', '.git', '.idea', '.vscode',
    '__pycache__', 'logs', 'temp', 'tmp', 'downloads',
}

EXCLUDED_FILE_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe',
    '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg', '.webp',
    '.mp4', '.mp3', '.wav', '.avi', '.mov',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.tar', '.gz',
    '.log', '.db', '.sqlite3', '.bak',
}

EXCLUDED_FILES = {
    'dump_django_project.py',  # exclude this script itself
    'db.sqlite3',              # exclude database file
}

# Files to always include (even if extension is excluded)
FORCE_INCLUDE = {
    'manage.py',
}

OUTPUT_FILE_PREFIX = 'django_project_dump'

# -----------------------------------

def should_exclude_file(file_path, root):
    """Check if file should be excluded based on name, extension, or parent directory."""
    filename = os.path.basename(file_path)
    if filename in EXCLUDED_FILES:
        return True
    if filename in FORCE_INCLUDE:
        return False
    # Exclude by extension
    ext = os.path.splitext(filename)[1].lower()
    if ext in EXCLUDED_FILE_EXTENSIONS:
        return True
    # Check any parent directory is in EXCLUDED_DIRS
    relative_path = os.path.relpath(root, start=PROJECT_ROOT)
    parts = relative_path.split(os.sep)
    for part in parts:
        if part in EXCLUDED_DIRS:
            return True
    return False

def write_file_content(out_file, file_path, root):
    """Write file header and content to output file."""
    rel_path = os.path.relpath(file_path, start=PROJECT_ROOT)
    out_file.write(f"\n{'='*80}\n")
    out_file.write(f"FILE: {rel_path}\n")
    out_file.write(f"{'='*80}\n\n")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        out_file.write(content)
        out_file.write("\n")
    except UnicodeDecodeError:
        out_file.write("[WARNING: Binary file, content not shown]\n")
    except Exception as e:
        out_file.write(f"[ERROR: Could not read file - {e}]\n")

def main():
    global PROJECT_ROOT
    PROJECT_ROOT = os.getcwd()
    print(f"Scanning project at: {PROJECT_ROOT}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{OUTPUT_FILE_PREFIX}_{timestamp}.txt"
    
    total_files = 0
    with open(output_filename, 'w', encoding='utf-8') as out_file:
        out_file.write(f"Django Project Dump\n")
        out_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_file.write(f"Project root: {PROJECT_ROOT}\n\n")

        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Modify dirs in-place to prevent walking into excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            for filename in files:
                file_path = os.path.join(root, filename)
                if should_exclude_file(file_path, root):
                    continue
                write_file_content(out_file, file_path, root)
                total_files += 1
                sys.stdout.write(f"\rProcessed: {total_files} files")
                sys.stdout.flush()
    
    print(f"\n\n✅ Done! Exported {total_files} files to: {output_filename}")

if __name__ == "__main__":
    main()
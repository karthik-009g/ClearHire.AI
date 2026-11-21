#!/usr/bin/env python3
"""
scripts/verify_mirror_parity.py
================================================================================
ClearHire.AI — Dual Repository Mirror Parity Verification Engine

Verifies 100% SHA-256 parity between the root repository (`C:\\Clear_Hire.AI`)
and the `job_automate/` subproject mirror across all tracked git files and
source subtrees.

Usage:
    python scripts/verify_mirror_parity.py [--verbose] [--all]
================================================================================
"""

import os
import sys
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Set


ROOT_DIR = Path(__file__).resolve().parent.parent
MIRROR_DIR = ROOT_DIR / "job_automate"

# Directories/files to exclude from whole-tree filesystem scans (runtime & caches)
EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".next",
    ".run",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "venv",
    ".venv",
    "storage",
    "_local_backups",
    ".agents",
    ".codex",
    ".chrome-temp",
}

EXCLUDE_FILES = {
    "tsconfig.tsbuildinfo",
    ".DS_Store",
    "Thumbs.db",
}


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file with binary read."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_git_tracked_files(repo_path: Path) -> List[str]:
    """Retrieves list of files tracked by git in the specified directory."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    except Exception as e:
        print(f"[WARN] Failed to query git ls-files for {repo_path}: {e}", file=sys.stderr)
        return []


def scan_mirrored_subtrees(root_path: Path, mirror_path: Path) -> Set[str]:
    """
    Scans project subtrees on disk that are mirrored, excluding runtime/caches.
    Prunes excluded directories using os.walk for instant traversal across root and mirror.
    """
    scanned_relpaths: Set[str] = set()
    subtrees = ["backend", "frontend", "deployment", "extension", "scripts", "docs"]

    for base in (mirror_path, root_path):
        for sub in subtrees:
            sub_dir = base / sub
            if not sub_dir.exists():
                continue
            for dirpath, dirnames, filenames in os.walk(sub_dir):
                dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
                for f in filenames:
                    if f in EXCLUDE_FILES:
                        continue
                    p = Path(dirpath) / f
                    rel = p.relative_to(base).as_posix()
                    parts = set(rel.split("/"))
                    if any(ex in parts for ex in EXCLUDE_DIRS) or "storage" in parts:
                        continue
                    scanned_relpaths.add(rel)

    # Add root config files
    for root_file in [
        "README.md",
        "TEST_READY.md",
        "TEST_INFRA.md",
        ".gitignore",
        ".dockerignore",
        ".env.example",
        "pytest.ini",
    ]:
        if (mirror_path / root_file).is_file() or (root_path / root_file).is_file():
            scanned_relpaths.add(root_file)

    return scanned_relpaths


def categorize_path(path: str) -> str:
    """Categorizes a relative file path for tabular reporting."""
    if path.startswith("backend/"):
        return "Backend (API/Services/Tests)"
    elif path.startswith("frontend/"):
        return "Frontend (UI/3D/Components)"
    elif path.startswith("deployment/"):
        return "Deployment & Manifests"
    elif path.startswith("extension/"):
        return "Browser Extension (MV3)"
    elif path.startswith("scripts/"):
        return "Automation & Benchmarks"
    elif path.startswith("docs/"):
        return "Architecture Documentation"
    else:
        return "Root Project Configuration"


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    all_mode = "--all" in sys.argv

    if not MIRROR_DIR.exists():
        print(f"[ERROR] Mirror directory not found: {MIRROR_DIR}", file=sys.stderr)
        return 1

    print("=" * 100)
    print(" CLEAR_HIRE.AI — DUAL REPOSITORY MIRROR PARITY VERIFICATION")
    print("=" * 100)
    print(f" Root Repository   : {ROOT_DIR}")
    print(f" Mirror Repository : {MIRROR_DIR}")

    # 1. Gather files to verify
    git_tracked = get_git_tracked_files(MIRROR_DIR)
    scanned_files = scan_mirrored_subtrees(ROOT_DIR, MIRROR_DIR)

    # Union of git tracked and scanned project files (ensures 100% coverage)
    all_files_to_verify = sorted(set(git_tracked) | scanned_files)

    print(f" Tracked in Git    : {len(git_tracked)} files")
    print(f" Mirrored Files    : {len(all_files_to_verify)} total files scheduled for verification")
    print("-" * 100)

    category_counts: Dict[str, Dict[str, int]] = {}
    mismatches: List[Tuple[str, str, str]] = []
    missing_in_root: List[str] = []
    missing_in_mirror: List[str] = []

    for rel_path in all_files_to_verify:
        cat = categorize_path(rel_path)
        if cat not in category_counts:
            category_counts[cat] = {"total": 0, "match": 0, "mismatch": 0, "missing": 0}

        category_counts[cat]["total"] += 1

        root_file = ROOT_DIR / rel_path
        mirror_file = MIRROR_DIR / rel_path

        if not root_file.exists():
            category_counts[cat]["missing"] += 1
            missing_in_root.append(rel_path)
            continue

        if not mirror_file.exists():
            category_counts[cat]["missing"] += 1
            missing_in_mirror.append(rel_path)
            continue

        root_hash = compute_sha256(root_file)
        mirror_hash = compute_sha256(mirror_file)

        if root_hash == mirror_hash:
            category_counts[cat]["match"] += 1
            if verbose:
                print(f"  [PASS] {cat:<30} | {rel_path} ({root_hash[:8]}...)")
        else:
            category_counts[cat]["mismatch"] += 1
            mismatches.append((rel_path, root_hash, mirror_hash))

    print(f"{'Category / Subsystem':<34} | {'Total':<6} | {'Matched':<7} | {'Mismatch':<8} | {'Missing':<7} | {'Parity %':<8}")
    print("-" * 100)

    total_files = 0
    total_matched = 0
    total_mismatch = 0
    total_missing = 0

    for cat, counts in sorted(category_counts.items()):
        tot = counts["total"]
        mat = counts["match"]
        mis = counts["mismatch"]
        ms = counts["missing"]
        pct = (mat / tot * 100.0) if tot > 0 else 0.0

        total_files += tot
        total_matched += mat
        total_mismatch += mis
        total_missing += ms

        status_flag = "PASS" if mat == tot else "FAIL"
        print(f"{cat:<34} | {tot:<6} | {mat:<7} | {mis:<8} | {ms:<7} | {pct:>6.1f}% [{status_flag}]")

    print("-" * 100)
    overall_pct = (total_matched / total_files * 100.0) if total_files > 0 else 0.0
    print(f"{'OVERALL REPOSITORY SUMMARY':<34} | {total_files:<6} | {total_matched:<7} | {total_mismatch:<8} | {total_missing:<7} | {overall_pct:>6.1f}%")
    print("=" * 100)

    # Report discrepancies if any
    if missing_in_root:
        print("\n[ERROR] Missing in Root Repository:")
        for p in missing_in_root:
            print(f"  - {p}")

    if missing_in_mirror:
        print("\n[ERROR] Missing in Mirror Repository:")
        for p in missing_in_mirror:
            print(f"  - {p}")

    if mismatches:
        print("\n[ERROR] SHA-256 Hash Mismatches:")
        for p, r_h, m_h in mismatches:
            print(f"  - {p}")
            print(f"      Root SHA-256  : {r_h}")
            print(f"      Mirror SHA-256: {m_h}")

    if total_mismatch == 0 and total_missing == 0 and overall_pct == 100.0:
        print(f"\n[SUCCESS] 100% SHA-256 Parity Confirmed across all {total_matched} files between root and job_automate/ mirror.\n")
        return 0
    else:
        print(f"\n[FAILURE] Parity check failed with {total_mismatch} mismatches and {total_missing} missing files.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

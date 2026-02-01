#!/usr/bin/env python3
"""
Import circuit SVGs for 2026 F1 season from julesr0y/f1-circuits-svg.
Only copies the circuits we need, keeping the repo clean.

Usage:
    python scripts/import_circuits_2026.py [--variant white|black|white-outline|black-outline]
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Configuration
REPO_URL = "https://github.com/julesr0y/f1-circuits-svg.git"
DEFAULT_VARIANT = "white"  # white, black, white-outline, black-outline

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
MAP_FILE = PROJECT_ROOT / "docs" / "circuits_2026_map.json"
OUTPUT_DIR = PROJECT_ROOT / "static" / "img" / "circuits" / "svg"
DATA_FILE = PROJECT_ROOT / "data" / "f1calendar_2026.json"


def load_circuit_map():
    """Load the circuit mapping configuration."""
    with open(MAP_FILE) as f:
        data = json.load(f)
    return data["circuits"]


def load_race_slugs():
    """Load race slugs from our 2026 calendar data."""
    with open(DATA_FILE) as f:
        races = json.load(f)
    return {race["slug"]: race for race in races}


def clone_repo(temp_dir):
    """Clone the SVG circuits repo to a temp directory."""
    print(f"Cloning {REPO_URL}...")
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, temp_dir],
        check=True,
        capture_output=True,
    )
    print("Clone complete.")


def import_circuits(variant=DEFAULT_VARIANT):
    """Main import function."""
    circuit_map = load_circuit_map()
    race_slugs = load_race_slugs()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Track results
    found = []
    missing = []
    ambiguous = []

    # Clone repo to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        clone_repo(temp_dir)

        source_dir = Path(temp_dir) / "circuits" / variant

        if not source_dir.exists():
            print(f"Error: Variant '{variant}' not found. Available: white, black, white-outline, black-outline")
            sys.exit(1)

        # Process each race in our calendar
        for slug, race in race_slugs.items():
            if slug not in circuit_map:
                missing.append({
                    "slug": slug,
                    "name": race["name"],
                    "circuit": race["circuit"],
                    "reason": "No mapping defined"
                })
                continue

            mapping = circuit_map[slug]
            svg_file = mapping["svg_file"]
            source_path = source_dir / svg_file

            if not source_path.exists():
                # Try to find alternatives
                base_name = mapping["source_id"]
                alternatives = list(source_dir.glob(f"{base_name}*.svg"))

                if alternatives:
                    ambiguous.append({
                        "slug": slug,
                        "name": race["name"],
                        "expected": svg_file,
                        "alternatives": [a.name for a in alternatives]
                    })
                else:
                    missing.append({
                        "slug": slug,
                        "name": race["name"],
                        "circuit": race["circuit"],
                        "reason": f"SVG file not found: {svg_file}"
                    })
                continue

            # Copy the file with our slug as filename
            dest_path = OUTPUT_DIR / f"{slug}.svg"
            shutil.copy2(source_path, dest_path)
            found.append({
                "slug": slug,
                "name": race["name"],
                "source": svg_file
            })

    # Print report
    print("\n" + "=" * 60)
    print("CIRCUIT IMPORT REPORT")
    print("=" * 60)

    print(f"\n✓ FOUND AND COPIED ({len(found)}):")
    for item in found:
        print(f"  {item['slug']:20} <- {item['source']:25} ({item['name']})")

    if missing:
        print(f"\n✗ MISSING ({len(missing)}):")
        for item in missing:
            print(f"  {item['slug']:20} - {item['name']} ({item.get('circuit', 'N/A')})")
            print(f"    Reason: {item['reason']}")

    if ambiguous:
        print(f"\n? AMBIGUOUS ({len(ambiguous)}):")
        for item in ambiguous:
            print(f"  {item['slug']:20} - {item['name']}")
            print(f"    Expected: {item['expected']}")
            print(f"    Found alternatives: {', '.join(item['alternatives'])}")

    print("\n" + "=" * 60)
    print(f"Summary: {len(found)} copied, {len(missing)} missing, {len(ambiguous)} ambiguous")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)

    return found, missing, ambiguous


if __name__ == "__main__":
    variant = DEFAULT_VARIANT

    # Parse simple --variant argument
    if len(sys.argv) > 1:
        if sys.argv[1] == "--variant" and len(sys.argv) > 2:
            variant = sys.argv[2]
        elif sys.argv[1] in ["white", "black", "white-outline", "black-outline"]:
            variant = sys.argv[1]
        elif sys.argv[1] in ["--help", "-h"]:
            print(__doc__)
            sys.exit(0)

    print(f"Using variant: {variant}")
    import_circuits(variant)

#!/usr/bin/env python3
"""
Convert SVG circuit images to pixelated PNG versions.

Requirements:
    pip install cairosvg pillow

If dependencies are not available, the script will skip gracefully.

Usage:
    python scripts/render_pixel_from_svg.py [--size 64] [--color "#f59e0b"]
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SVG_DIR = PROJECT_ROOT / "static" / "img" / "circuits" / "svg"
PIXEL_DIR = PROJECT_ROOT / "static" / "img" / "circuits" / "pixel"

DEFAULT_SIZE = 128  # Output size (will be small for pixel look)
DEFAULT_COLOR = "#f59e0b"  # Accent color to tint the circuit


def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import cairosvg
        from PIL import Image
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install cairosvg pillow")
        print("On Linux you may also need: apt-get install libcairo2-dev")
        return False


def convert_svg_to_pixel_png(svg_path, output_path, size=DEFAULT_SIZE):
    """Convert an SVG to a small pixelated PNG."""
    import cairosvg
    from PIL import Image
    import io

    # Render SVG to PNG at target size (small = pixelated look)
    png_data = cairosvg.svg2png(
        url=str(svg_path),
        output_width=size,
        output_height=size,
    )

    # Load with PIL and save
    img = Image.open(io.BytesIO(png_data))

    # Convert to RGBA if needed
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Save as PNG
    img.save(output_path, "PNG")
    return True


def main(size=DEFAULT_SIZE):
    """Convert all SVGs in the svg directory to pixel PNGs."""
    if not check_dependencies():
        print("\nSkipping pixel conversion (dependencies not available).")
        print("Circuits will use SVG fallback in templates.")
        return

    PIXEL_DIR.mkdir(parents=True, exist_ok=True)

    svg_files = list(SVG_DIR.glob("*.svg"))
    if not svg_files:
        print(f"No SVG files found in {SVG_DIR}")
        print("Run import_circuits_2026.py first.")
        return

    print(f"Converting {len(svg_files)} SVGs to pixel PNGs (size: {size}x{size})...")

    converted = 0
    failed = 0

    for svg_path in svg_files:
        output_path = PIXEL_DIR / f"{svg_path.stem}.png"
        try:
            convert_svg_to_pixel_png(svg_path, output_path, size)
            print(f"  ✓ {svg_path.name} -> {output_path.name}")
            converted += 1
        except Exception as e:
            print(f"  ✗ {svg_path.name}: {e}")
            failed += 1

    print(f"\nDone: {converted} converted, {failed} failed")
    print(f"Output: {PIXEL_DIR}")


if __name__ == "__main__":
    size = DEFAULT_SIZE

    # Parse simple --size argument
    if "--size" in sys.argv:
        idx = sys.argv.index("--size")
        if idx + 1 < len(sys.argv):
            try:
                size = int(sys.argv[idx + 1])
            except ValueError:
                pass

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    main(size)

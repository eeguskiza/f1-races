"""Template tags for circuit images."""
from django import template
from django.conf import settings
from django.templatetags.static import static
from pathlib import Path

register = template.Library()


@register.simple_tag
def circuit_image_url(slug):
    """
    Return the URL for a circuit image, checking PNG then SVG.
    Returns empty string if no image exists.

    Usage: {% circuit_image_url race.slug as circuit_url %}
    """
    # Check for PNG first (pixel version)
    png_path = Path(settings.BASE_DIR) / "static" / "img" / "circuits" / "pixel" / f"{slug}.png"
    if png_path.exists():
        return static(f"img/circuits/pixel/{slug}.png")

    # Fall back to SVG
    svg_path = Path(settings.BASE_DIR) / "static" / "img" / "circuits" / "svg" / f"{slug}.svg"
    if svg_path.exists():
        return static(f"img/circuits/svg/{slug}.svg")

    return ""


@register.inclusion_tag("predictions/_circuit_slot.html")
def circuit_slot(slug, css_class=""):
    """
    Render a circuit image slot with fallback placeholder.

    Usage: {% circuit_slot race.slug "track-slot" %}
    """
    # Check for PNG first (pixel version)
    png_path = Path(settings.BASE_DIR) / "static" / "img" / "circuits" / "pixel" / f"{slug}.png"
    if png_path.exists():
        return {
            "image_url": static(f"img/circuits/pixel/{slug}.png"),
            "has_image": True,
            "css_class": css_class,
        }

    # Fall back to SVG
    svg_path = Path(settings.BASE_DIR) / "static" / "img" / "circuits" / "svg" / f"{slug}.svg"
    if svg_path.exists():
        return {
            "image_url": static(f"img/circuits/svg/{slug}.svg"),
            "has_image": True,
            "css_class": css_class,
        }

    return {
        "image_url": "",
        "has_image": False,
        "css_class": css_class,
    }

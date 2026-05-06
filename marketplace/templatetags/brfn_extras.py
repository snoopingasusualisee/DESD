"""
Template helpers used across BRFN templates.

The big one here is `product_image_url`: producers may or may not have uploaded
a real product photo. When they haven't, we fall back to a curated static image
shipped with the project, matched by product name slug. As a last resort we
return a generic placeholder so cards never render an empty <img>.

Why a templatetag rather than logic in the model? Because the static fallback
depends on `STATIC_URL`, which is a presentation concern, and we want the same
fallback rule applied uniformly to every template that shows a product card.
"""
import os
import re
from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


# Built once at import. We deliberately don't hit the filesystem on every
# request — that would be wasted work in a hot path (every product card on
# every browse page). If you add a new file under static/images/products/
# you'll need to restart the server, which matches Django's behaviour for
# all static files.
_PRODUCTS_DIR = os.path.join(settings.BASE_DIR, "static", "images", "products")
try:
    _AVAILABLE_PRODUCT_IMAGES = {
        f.lower() for f in os.listdir(_PRODUCTS_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    }
except (FileNotFoundError, OSError):
    _AVAILABLE_PRODUCT_IMAGES = set()


def _slugify_for_image(name: str) -> str:
    """
    Turn 'Bramley Apples' into 'bramley_apples', 'Pork Sausages (500g)' into
    'pork_sausages'. Underscores match the existing image filenames.
    """
    if not name:
        return ""
    cleaned = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "_", cleaned)


def _fallback_filename_for(name: str) -> str | None:
    """Return the matching static image filename, or None if nothing fits."""
    slug = _slugify_for_image(name)
    if not slug:
        return None

    # Try exact match first, then the "_2" variant (curated alternates), then
    # any image whose stem starts with the slug. Returning the first hit keeps
    # behaviour deterministic — sets are unordered, so we sort.
    candidates = [f"{slug}.jpg", f"{slug}_2.jpg", f"{slug}.png", f"{slug}.webp"]
    for candidate in candidates:
        if candidate in _AVAILABLE_PRODUCT_IMAGES:
            return candidate

    prefix = f"{slug}"
    for filename in sorted(_AVAILABLE_PRODUCT_IMAGES):
        stem, _ = os.path.splitext(filename)
        if stem.startswith(prefix):
            return filename

    return None


@register.simple_tag
def product_image_url(product) -> str:
    """
    Return a URL safe to drop straight into <img src="...">.

    Resolution order:
      1. Producer-uploaded image (Product.image)
      2. Curated static image matched on product name slug
      3. Generic placeholder shipped with the project

    Always returns a string, never None — templates can use this without an
    `{% if %}` guard.
    """
    if product is None:
        return static("images/products/_placeholder.svg")

    uploaded = getattr(product, "image", None)
    if uploaded:
        try:
            return uploaded.url
        except (ValueError, AttributeError):
            pass

    name = getattr(product, "name", "") or ""
    fallback = _fallback_filename_for(name)
    if fallback:
        return static(f"images/products/{fallback}")

    return static("images/products/_placeholder.svg")


@register.filter
def product_image(product) -> str:
    """Filter form so templates can write `{{ product|product_image }}`."""
    return product_image_url(product)

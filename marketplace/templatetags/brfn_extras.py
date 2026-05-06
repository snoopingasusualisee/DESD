"""
Template helpers used across BRFN templates.

Image fallback chain (works for products, recipes, stories):
  1. Producer-uploaded file (`obj.image`)
  2. Curated static image matched on the object's name/title slug
  3. Curated static image matched on a token contained in the name/title
     (so 'Free-range Eggs' still finds 'eggs.jpg')
  4. A category-themed fallback (e.g. recipes get a bakery/produce shot)
  5. The branded SVG placeholder

Why a templatetag rather than logic in the model? Because the static fallback
depends on `STATIC_URL`, which is a presentation concern, and we want the same
fallback rule applied uniformly to every template that shows an image card.
"""
import os
import random
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
    _AVAILABLE_PRODUCT_IMAGES = sorted(
        f for f in os.listdir(_PRODUCTS_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) and not f.startswith("_")
    )
except (FileNotFoundError, OSError):
    _AVAILABLE_PRODUCT_IMAGES = []

# Lookup index: stem -> filename, e.g. "carrots" -> "carrots.jpg"
_STEM_INDEX = {}
for fname in _AVAILABLE_PRODUCT_IMAGES:
    stem = os.path.splitext(fname)[0].lower()
    # Strip "_2" / "_3" suffixes so "carrots_2" still maps to the "carrots" stem
    base = re.sub(r"_\d+$", "", stem)
    _STEM_INDEX.setdefault(base, fname)
    _STEM_INDEX.setdefault(stem, fname)

# Curated themed fallbacks for non-product objects so recipes/stories never
# render the ugly grey placeholder.
_RECIPE_THEMES = [
    "sourdough_loaf.jpg", "scones.jpg", "wholemeal_bread.jpg", "croissants.jpg",
    "strawberry_jam.jpg", "elderflower_cordial.jpg", "honey.jpg", "butter.jpg",
]
_STORY_THEMES = [
    "carrots_2.jpg", "courgettes_2.jpg", "broccoli_2.jpg", "tomatoes.jpg",
    "potatoes_2.jpg", "eggs.jpg", "milk.jpg", "cheddar_2.jpg",
]
_PRODUCER_THEMES = _STORY_THEMES + ["lamb_chops.jpg", "chicken_breast_2.jpg"]


def _slugify(name: str) -> str:
    """'Bramley Apples' -> 'bramley_apples'."""
    if not name:
        return ""
    cleaned = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "_", cleaned)


def _tokens(name: str) -> list[str]:
    """'Free-range Eggs' -> ['free', 'range', 'eggs']."""
    if not name:
        return []
    return [t for t in re.split(r"[\W_]+", name.lower()) if t]


def _stable_pick(name: str, options: list[str]) -> str:
    """
    Deterministically pick one option for a given name. Same name => same image
    every page render, so the UI doesn't shuffle on refresh.
    """
    if not options:
        return "_placeholder.svg"
    rng = random.Random(name or "default")
    return rng.choice(options)


def _match_filename(name: str) -> str | None:
    """Find the best static image for a name, or None."""
    if not name:
        return None

    slug = _slugify(name)

    # 1) Exact stem match: 'bramley_apples' -> 'bramley_apples.jpg'
    if slug in _STEM_INDEX:
        return _STEM_INDEX[slug]

    # 2) Any single token matches a stem: 'Free Range Eggs' -> 'eggs.jpg'
    for token in _tokens(name):
        if len(token) < 3:
            continue
        if token in _STEM_INDEX:
            return _STEM_INDEX[token]

    # 3) Any stem is contained in the slug, e.g. 'organic_carrots_500g' -> carrots
    for stem, fname in _STEM_INDEX.items():
        if len(stem) >= 4 and stem in slug:
            return fname

    return None


def _resolve_image(obj, themes: list[str], name_attrs: tuple[str, ...]) -> str:
    """
    Shared resolution logic for product/recipe/story.

    `name_attrs` is the order of attributes to try when extracting the object
    name (products use .name, recipes/stories use .title).
    """
    if obj is None:
        return static("images/products/_placeholder.svg")

    uploaded = getattr(obj, "image", None)
    if uploaded:
        try:
            return uploaded.url
        except (ValueError, AttributeError):
            pass

    name = ""
    for attr in name_attrs:
        value = getattr(obj, attr, None)
        if value:
            name = str(value)
            break

    matched = _match_filename(name)
    if matched:
        return static(f"images/products/{matched}")

    if themes:
        return static(f"images/products/{_stable_pick(name, themes)}")

    return static("images/products/_placeholder.svg")


@register.simple_tag
def product_image_url(product) -> str:
    """Resolve an image URL for a Product. Always returns a string."""
    return _resolve_image(product, themes=[], name_attrs=("name",))


@register.simple_tag
def recipe_image_url(recipe) -> str:
    """Resolve an image URL for a Recipe. Falls back to a curated bakery photo."""
    return _resolve_image(recipe, themes=_RECIPE_THEMES, name_attrs=("title", "name"))


@register.simple_tag
def story_image_url(story) -> str:
    """Resolve an image URL for a Story. Falls back to a curated produce photo."""
    return _resolve_image(story, themes=_STORY_THEMES, name_attrs=("title", "name"))


@register.simple_tag
def producer_image_url(producer) -> str:
    """Resolve a hero image for a Producer profile. Always uses a themed photo."""
    if producer is None:
        return static("images/products/_placeholder.svg")
    name = (
        getattr(producer, "username", "")
        or f"{getattr(producer, 'first_name', '')} {getattr(producer, 'last_name', '')}"
    )
    return static(f"images/products/{_stable_pick(name, _PRODUCER_THEMES)}")


@register.simple_tag
def initials(*parts) -> str:
    """
    Build initials from names: initials('John', 'Doe') -> 'JD',
    initials('alice') -> 'A'. Used for circular avatars where we don't have
    a profile picture.
    """
    letters = []
    for part in parts:
        if part:
            piece = str(part).strip()
            if piece:
                letters.append(piece[0].upper())
    if not letters:
        return "?"
    return "".join(letters[:2])


@register.filter
def product_image(product) -> str:
    """Filter form so templates can write `{{ product|product_image }}`."""
    return product_image_url(product)

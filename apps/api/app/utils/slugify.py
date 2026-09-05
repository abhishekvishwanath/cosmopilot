import re


def slugify(value: str) -> str:
    """URL-safe slug from a name, e.g. 'Porcelain Veneers' -> 'porcelain-veneers'."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")

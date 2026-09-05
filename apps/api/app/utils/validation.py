import re


def has_min_digits(value: str, minimum: int) -> bool:
    """True if `value` contains at least `minimum` digit characters."""
    return len(re.sub(r"\D", "", value)) >= minimum

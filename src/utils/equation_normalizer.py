import re

ZERO_WIDTH_PATTERN = re.compile(r"[\u200B\u200C\u200D\u2060\uFEFF]")


def normalize_equation_text(text):
    """Remove invisible characters that can break equation parsing."""
    if not text:
        return text
    normalized = ZERO_WIDTH_PATTERN.sub("", text)
    normalized = normalized.replace("\u00A0", " ").replace("\u3000", " ")
    return normalized

import re
import unicodedata

ZERO_WIDTH_PATTERN = re.compile(r"[\u200B\u200C\u200D\u2060\uFEFF]")
# Bar-like Unicode marks/symbols that users may type in variable names.
# U+0304: combining macron, U+00AF: macron, U+203E: overline,
# U+02C9: modifier letter macron, U+FFE3: fullwidth macron.
BAR_MARKS_PATTERN = re.compile(r"[\u0304\u00AF\u203E\u02C9\uFFE3]")


def normalize_variable_name(name: str) -> str:
    """Normalize variable names for parser use (e.g. Rȳ -> Ry_bar)."""
    if not name:
        return ""
    text = unicodedata.normalize("NFD", str(name))
    text = ZERO_WIDTH_PATTERN.sub("", text)
    text = text.replace("\u00A0", " ").replace("\u3000", " ")
    text = BAR_MARKS_PATTERN.sub("_bar", text)
    text = re.sub(r"_bar(?:_bar)+", "_bar", text)
    return text.strip()


def normalize_equation_text(text):
    """Remove invisible characters that can break equation parsing."""
    if not text:
        return text
    normalized = unicodedata.normalize("NFD", text)
    normalized = ZERO_WIDTH_PATTERN.sub("", normalized)
    normalized = normalized.replace("\u00A0", " ").replace("\u3000", " ")
    normalized = BAR_MARKS_PATTERN.sub("_bar", normalized)
    normalized = re.sub(r"_bar(?:_bar)+", "_bar", normalized)
    return normalized

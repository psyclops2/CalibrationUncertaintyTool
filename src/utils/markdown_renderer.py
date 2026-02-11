from __future__ import annotations

import markdown


def render_markdown_to_html(text: str) -> str:
    """Render Markdown text to HTML.

    Args:
        text: Markdown source text.

    Returns:
        Rendered HTML string. Empty string is returned when the input is blank
        or contains only whitespace.
    """
    if text is None:
        return ""

    stripped = text.strip()
    if not stripped:
        return ""

    # Also treat plain newlines as <br> so line breaks in the editor are preserved.
    return markdown.markdown(stripped, extensions=["extra", "nl2br"])

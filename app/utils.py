import markdown
from html import escape


def render_markdown(text: str, safe: bool = True) -> str:
    """
    Render markdown text to HTML with security considerations.

    Args:
        text: The markdown text to render
        safe: If True, escape HTML to prevent XSS attacks

    Returns:
        Rendered HTML string
    """
    if not text:
        return ""

    # Escape HTML to prevent XSS if safe mode is enabled
    if safe:
        text = escape(text)

    # Configure markdown with safe extensions
    md = markdown.Markdown(
        extensions=[
            'markdown.extensions.fenced_code',
            'markdown.extensions.tables',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists'
        ],
        output_format='html5'
    )

    # Render markdown to HTML
    html = md.convert(text)

    # Mark the HTML as safe for Jinja2
    from markupsafe import Markup
    return Markup(html) 
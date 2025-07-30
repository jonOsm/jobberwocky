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

    # Escape HTML to prevent XSS attacks
    # We need to be careful not to escape markdown syntax characters
    if safe:
        # Escape HTML tags but preserve markdown syntax
        import re
        # Escape HTML tags but not markdown syntax
        text = re.sub(r'<([^>]+)>', r'&lt;\1&gt;', text)

    # Configure markdown with essential extensions
    md = markdown.Markdown(
        extensions=[
            'markdown.extensions.fenced_code',      # Code blocks with ```
            'markdown.extensions.tables',           # Tables
            'markdown.extensions.nl2br',            # Newlines to <br>
            'markdown.extensions.sane_lists',       # Better list handling
            'markdown.extensions.attr_list',        # Attribute lists
        ],
        output_format='html5'
    )

    # Render markdown to HTML
    html = md.convert(text)

    # Mark the HTML as safe for Jinja2
    from markupsafe import Markup
    return Markup(html) 
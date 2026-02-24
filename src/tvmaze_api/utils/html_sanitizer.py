from html_sanitizer import Sanitizer  # type: ignore[import-untyped]


# Sanitize HTML for show & episode summaries (we don't trust TVmaze, do we)
def sanitize_html(html: str) -> str:
    sanitizer = Sanitizer(
        {
            "tags": {  # tags retained in sanitized html; defaults minus <a>
                "h1",
                "h2",
                "h3",
                "strong",
                "em",
                "p",
                "ul",
                "ol",
                "li",
                "br",
                "sub",
                "sup",
                "hr",
            },
            "attributes": {},
            "empty": {"hr", "br"},  # tags retained even if empty
            "separate": {"p", "li"},  # will not be merged with siblings
            "whitespace": set(),
            "keep_typographic_whitespace": True,
        }
    )
    return str(sanitizer.sanitize(html))

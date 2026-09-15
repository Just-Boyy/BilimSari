"""Dars kontenti (HTML) uchun XSS himoyasi — faqat ruxsat etilgan teg/atributlar qoldiriladi."""

import nh3

ALLOWED_TAGS = {
    "p", "b", "i", "strong", "em", "u", "br", "img", "table", "thead", "tbody",
    "tr", "td", "th", "code", "pre", "a", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "span", "sub", "sup",
}

ALLOWED_ATTRIBUTES = {
    "img": {"src", "alt", "width", "height"},
    "a": {"href", "title", "target"},
    "span": {"class"},
    "code": {"class"},
}


def sanitize_html(raw_html: str) -> str:
    return nh3.clean(raw_html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

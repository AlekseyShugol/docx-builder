"""Парсер HTML и Markdown в структурированные блоки документа."""

from .html_to_md import html_to_markdown_if_needed
from .markup import clean_inline_markdown, parse_markup_to_blocks

__all__ = [
    "clean_inline_markdown",
    "html_to_markdown_if_needed",
    "parse_markup_to_blocks",
]

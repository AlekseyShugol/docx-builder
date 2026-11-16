"""Движок генерации и подсчёта страниц .docx."""

from .docx_writer import build_docx_bytes, export_to_docx
from .page_counter import count_pdf_pages_via_libreoffice, estimate_docx_pages

__all__ = [
    "build_docx_bytes",
    "count_pdf_pages_via_libreoffice",
    "estimate_docx_pages",
    "export_to_docx",
]

import io
import os
import tempfile

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

from ..config import JAVA_KEYWORDS, TOKEN_PATTERN
from .page_counter import count_pdf_pages_via_libreoffice, estimate_docx_pages
from .styles import (
    add_page_number_footer,
    keep_row_with_next,
    prevent_row_split,
    set_cell_background,
    set_cell_margins,
    set_docx_font_tnr,
    set_repeat_table_header,
    set_table_borders,
)

_USABLE_WIDTH_INCHES = 6.7


def _configure_page_setup(doc: Document) -> None:
    for section in doc.sections:
        section.page_width = Inches(8.27)     # A4
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.79)     # 20 мм
        section.bottom_margin = Inches(0.79)  # 20 мм
        section.left_margin = Inches(0.98)    # 25 мм
        section.right_margin = Inches(0.59)   # 15 мм
        add_page_number_footer(section)

    style_normal = doc.styles["Normal"]
    style_normal.font.name = "Times New Roman"
    style_normal.font.size = Pt(14)
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(4)


def _add_h1(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    set_docx_font_tnr(r, size=16, bold=True)
    p_pr = p._p.get_or_add_pPr()
    p_bdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="8" w:space="3" w:color="000000"/></w:pBdr>'
    )
    p_pr.append(p_bdr)


def _add_h2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    set_docx_font_tnr(r, size=14, bold=True)


def _add_body(doc: Document, text: str, indent: bool = True, bold_prefix: str | None = None) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    if indent:
        p.paragraph_format.first_line_indent = Inches(0.49)
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        set_docx_font_tnr(rb, size=14, bold=True)
    r = p.add_run(text)
    set_docx_font_tnr(r, size=14)


def _add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Inches(0.49)
    p.paragraph_format.first_line_indent = Inches(-0.2)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    rb_bul = p.add_run("• ")
    set_docx_font_tnr(rb_bul, size=14, bold=True)
    if ":" in text and text.index(":") < 45:
        head, rest = text.split(":", 1)
        r_h = p.add_run(head + ":")
        set_docx_font_tnr(r_h, size=14, bold=True)
        r_b = p.add_run(rest)
        set_docx_font_tnr(r_b, size=14)
    else:
        r = p.add_run(text)
        set_docx_font_tnr(r, size=14)


def _add_text_lines(doc: Document, text: str) -> None:
    for raw_ln in text.split("\n"):
        ln = raw_ln.strip()
        if not ln:
            continue
        if ln.startswith("• ") or ln.startswith("- ") or ln.startswith("* "):
            _add_bullet(doc, ln[2:].strip())
        else:
            _add_body(doc, ln, indent=True)


def _add_code_table(doc: Document, title_label: str, code_text: str, highlight_code: bool = True) -> None:
    if not code_text.strip():
        return
    table = doc.add_table(rows=2, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(_USABLE_WIDTH_INCHES)

    hdr_cell = table.cell(0, 0)
    hdr_cell.width = Inches(_USABLE_WIDTH_INCHES)
    set_cell_background(hdr_cell, "E6ECF2")
    set_cell_margins(hdr_cell, top=50, bottom=50, left=120, right=120)
    hp = hdr_cell.paragraphs[0]
    hp.paragraph_format.space_after = Pt(0)
    hr = hp.add_run(title_label)
    set_docx_font_tnr(hr, size=14, bold=True, italic=True, color=RGBColor(0x1A, 0x2B, 0x4C))

    cell = table.cell(1, 0)
    cell.width = Inches(_USABLE_WIDTH_INCHES)
    set_cell_background(cell, "F8F9FA")
    set_cell_margins(cell, top=70, bottom=70, left=120, right=120)

    set_table_borders(
        table,
        top="778899",
        bottom="778899",
        left="2B4C7E",
        left_sz=18,
        right="778899",
        inside_h="B0BEC5",
        inside_v=None,
    )

    prevent_row_split(table.rows[0])
    keep_row_with_next(table.rows[0])
    prevent_row_split(table.rows[1])

    for idx, line in enumerate(code_text.split("\n")):
        p = cell.paragraphs[0] if idx == 0 else cell.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05
        ln_run = p.add_run(f"{idx + 1:2d} | ")
        set_docx_font_tnr(ln_run, size=14, color=RGBColor(0x77, 0x77, 0x77))

        if not highlight_code:
            r = p.add_run(line)
            set_docx_font_tnr(r, size=14, color=RGBColor(0x11, 0x11, 0x11))
            continue

        for tok in TOKEN_PATTERN.findall(line):
            if tok.startswith("//"):
                r = p.add_run(tok)
                set_docx_font_tnr(r, size=14, italic=True, color=RGBColor(0x2E, 0x6B, 0x2E))
            elif tok.startswith('"') or tok.startswith("'"):
                r = p.add_run(tok)
                set_docx_font_tnr(r, size=14, color=RGBColor(0x8B, 0x26, 0x35))
            elif tok in JAVA_KEYWORDS:
                r = p.add_run(tok)
                set_docx_font_tnr(r, size=14, bold=True, color=RGBColor(0x00, 0x33, 0x99))
            elif tok[0].isdigit():
                r = p.add_run(tok)
                set_docx_font_tnr(r, size=14, color=RGBColor(0x00, 0x5C, 0x5C))
            else:
                r = p.add_run(tok)
                set_docx_font_tnr(r, size=14, color=RGBColor(0x11, 0x11, 0x11))

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)


def _add_data_table(doc: Document, title: str, headers: list[str], rows: list[list[str]]) -> None:
    col_count = max(len(headers), max((len(r) for r in rows), default=0))
    if col_count == 0:
        return

    if title.strip():
        _add_h2(doc, title.strip())

    all_rows = [headers] + rows if headers else rows
    if not all_rows:
        return

    tbl = doc.add_table(rows=len(all_rows), cols=col_count)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    set_table_borders(tbl, top="556677", bottom="556677", left="556677", right="556677", inside_h="B0BEC5", inside_v="B0BEC5")

    col_width = Inches(_USABLE_WIDTH_INCHES / col_count)

    for r_i, row_data in enumerate(all_rows):
        row = tbl.rows[r_i]
        prevent_row_split(row)
        is_header = bool(headers) and r_i == 0
        if is_header:
            set_repeat_table_header(row)
            keep_row_with_next(row)

        for c_i in range(col_count):
            cell = tbl.cell(r_i, c_i)
            cell.width = col_width
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            if is_header:
                set_cell_background(cell, "E6ECF2")
            elif r_i % 2 == 0:
                set_cell_background(cell, "FAFBFD")

            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if is_header else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.1
            val = row_data[c_i] if c_i < len(row_data) else ""
            r = p.add_run(val)
            set_docx_font_tnr(
                r,
                size=14,
                bold=is_header,
                color=RGBColor(0x1A, 0x2B, 0x4C) if is_header else RGBColor(0, 0, 0),
            )

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)


def _add_even_filler_page(doc: Document) -> None:
    doc.add_page_break()
    _add_h1(doc, "Лист самоконтроля и заметок")
    _add_body(
        doc,
        "Используйте данную страницу для фиксации граничных тестов, оценки сложности по времени и памяти, "
        "а также заметок по итогам проверки решений.",
    )
    tbl = doc.add_table(rows=16, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    set_table_borders(tbl, top="000000", bottom="000000", left="000000", right="000000", inside_h="000000", inside_v="000000")

    col_w = [Inches(1.2), Inches(2.0), Inches(3.5)]
    prevent_row_split(tbl.rows[0])
    set_repeat_table_header(tbl.rows[0])
    keep_row_with_next(tbl.rows[0])

    for c_i, h_t in enumerate(["№ задачи", "Статус проверки", "Примечания"]):
        cell = tbl.cell(0, c_i)
        cell.width = col_w[c_i]
        set_cell_background(cell, "E6ECF2")
        set_cell_margins(cell, top=60, bottom=60, left=90, right=90)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_t)
        set_docx_font_tnr(r, size=14, bold=True)

    for r_i in range(1, 16):
        prevent_row_split(tbl.rows[r_i])
        for c_i in range(3):
            cell = tbl.cell(r_i, c_i)
            cell.width = col_w[c_i]
            set_cell_margins(cell, top=50, bottom=50, left=90, right=90)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(" ")
            set_docx_font_tnr(r, size=14)


def _render_document(
    doc_title: str,
    doc_subtitle: str,
    blocks: list[dict],
    include_solutions: bool = True,
    append_even_filler: bool = False,
) -> Document:
    doc = Document()
    _configure_page_setup(doc)

    if doc_title.strip():
        tp = doc.add_paragraph()
        tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        tp.paragraph_format.space_after = Pt(6)
        tr = tp.add_run(doc_title.strip())
        set_docx_font_tnr(tr, size=16, bold=True)

    if doc_subtitle.strip():
        sp0 = doc.add_paragraph()
        sp0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sp0.paragraph_format.space_after = Pt(12)
        sr0 = sp0.add_run(doc_subtitle.strip())
        set_docx_font_tnr(sr0, size=14, italic=True)

    for blk in blocks:
        b_type = blk.get("type")
        if b_type == "page_break":
            doc.add_page_break()
        elif b_type == "heading":
            if blk.get("text", "").strip():
                _add_h1(doc, blk["text"].strip())
        elif b_type == "paragraph":
            _add_text_lines(doc, blk.get("text", ""))
        elif b_type == "code":
            _add_code_table(doc, blk.get("title", "Листинг кода") or "Листинг кода", blk.get("code", ""), True)
        elif b_type == "table":
            _add_data_table(
                doc,
                blk.get("title", ""),
                blk.get("headers", []),
                blk.get("rows", []),
            )
        elif b_type == "task":
            if blk.get("title", "").strip():
                _add_h2(doc, blk["title"].strip())
            _add_text_lines(doc, blk.get("condition", ""))
            if blk.get("io", "").strip():
                _add_code_table(doc, "Пример входных и выходных данных", blk["io"], False)
            if blk.get("hint", "").strip():
                _add_body(doc, blk["hint"].strip(), indent=False, bold_prefix="Рекомендация: ")
            if include_solutions and blk.get("solution", "").strip():
                _add_code_table(doc, "Решение", blk["solution"], True)

    if append_even_filler:
        _add_even_filler_page(doc)

    return doc


def export_to_docx(
    doc_title: str,
    doc_subtitle: str,
    blocks: list[dict],
    output_path: str,
    include_solutions: bool = True,
    append_even_filler: bool = False,
) -> int:
    """Генерирует .docx на диск и возвращает приблизительное число страниц."""
    doc = _render_document(doc_title, doc_subtitle, blocks, include_solutions, append_even_filler)
    doc.save(output_path)
    return estimate_docx_pages(doc)


def build_docx_bytes(
    doc_title: str,
    doc_subtitle: str,
    blocks: list[dict],
    include_solutions: bool = True,
    even_pages: bool = True,
) -> tuple[bytes, int, bool]:
    """Генерирует .docx в память; при even_pages=True добивает до чётного числа страниц."""
    doc = _render_document(doc_title, doc_subtitle, blocks, include_solutions, append_even_filler=False)
    est_pages = estimate_docx_pages(doc)

    buf = io.BytesIO()
    doc.save(buf)
    data = buf.getvalue()

    if not even_pages:
        return data, est_pages, False

    exact_pages: int | None = None
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        exact_pages = count_pdf_pages_via_libreoffice(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    pages = exact_pages if exact_pages is not None else est_pages
    if pages % 2 != 0:
        doc_even = _render_document(doc_title, doc_subtitle, blocks, include_solutions, append_even_filler=True)
        buf_even = io.BytesIO()
        doc_even.save(buf_even)
        return buf_even.getvalue(), pages + 1, True

    return data, pages, False

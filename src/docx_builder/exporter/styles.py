from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Pt, RGBColor


def set_docx_font_tnr(
    run,
    size: int = 14,
    bold: bool = False,
    italic: bool = False,
    color: RGBColor = RGBColor(0, 0, 0),
) -> None:
    """Устанавливает шрифт Times New Roman для run (включая кириллицу / cs)."""
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color
    r_pr = run._r.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.insert(0, r_fonts)
    r_fonts.set(qn("w:ascii"), "Times New Roman")
    r_fonts.set(qn("w:hAnsi"), "Times New Roman")
    r_fonts.set(qn("w:cs"), "Times New Roman")


def set_cell_background(cell, fill_hex: str) -> None:
    """Заливка фона ячейки таблицы."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_pr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))


def set_cell_margins(cell, top: int = 70, bottom: int = 70, left: int = 120, right: int = 120) -> None:
    """Внутренние отступы ячейки таблицы (в dxa)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = OxmlElement("w:tcMar")
    for side, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tc_mar.append(node)
    tc_pr.append(tc_mar)


def prevent_row_split(row) -> None:
    """Запрещает разрыв строки таблицы между страницами (w:cantSplit)."""
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:cantSplit")) is None:
        tr_pr.append(OxmlElement("w:cantSplit"))


def set_repeat_table_header(row) -> None:
    """Помечает строку как повторяющуюся шапку таблицы при переносе на новую страницу."""
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:tblHeader")) is None:
        tr_pr.append(OxmlElement("w:tblHeader"))


def keep_row_with_next(row) -> None:
    """Не отрывает строку таблицы (обычно шапку) от следующей строки."""
    for cell in row.cells:
        for p in cell.paragraphs:
            p.paragraph_format.keep_with_next = True


def set_table_borders(
    table,
    top: str = "778899",
    bottom: str = "778899",
    left: str = "778899",
    left_sz: int = 4,
    right: str = "778899",
    inside_h: str = "B0BEC5",
    inside_v: str | None = "B0BEC5",
) -> None:
    """Задаёт границы таблицы."""
    inside_v_xml = (
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{inside_v}"/>'
        if inside_v
        else '<w:insideV w:val="none"/>'
    )
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="{top}"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="{bottom}"/>
            <w:left w:val="single" w:sz="{left_sz}" w:space="0" w:color="{left}"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="{right}"/>
            <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{inside_h}"/>
            {inside_v_xml}
        </w:tblBorders>
    ''')
    table._tbl.tblPr.append(borders)


def add_page_number_footer(section) -> None:
    """Добавляет нумерацию страниц «Стр. N» в нижний колонтитул."""
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = fp.add_run("Стр. ")
    set_docx_font_tnr(r1, size=14, color=RGBColor(0x33, 0x33, 0x33))

    r_pg = fp.add_run()
    set_docx_font_tnr(r_pg, size=14, color=RGBColor(0x33, 0x33, 0x33))
    for xml_str in (
        r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"),
        r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls("w"),
        r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"),
        r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"),
    ):
        r_pg._r.append(parse_xml(xml_str))

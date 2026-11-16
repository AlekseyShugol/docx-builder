import math
import os
import re
import shutil
import subprocess
import tempfile

from docx.oxml.ns import qn


def estimate_docx_pages(doc) -> int:
    """Приблизительно оценивает число страниц документа A4 без LibreOffice."""
    usable_h = 727.9
    pages = 1
    y = 0.0
    for block in doc.element.body:
        tag = block.tag.split("}")[-1]
        if tag == "p":
            if 'w:type="page"' in block.xml:
                pages += 1
                y = 0.0
                continue
            txt = "".join(block.itertext())
            lines = max(1, math.ceil(len(txt) / 70.0)) if txt.strip() else 1
            h = lines * 16.5 + 6.0
        elif tag == "tbl":
            rows_cnt = len(block.findall(".//" + qn("w:tr")))
            txt = "".join(block.itertext())
            h = (txt.count("\n") + rows_cnt) * 15.8 + 18.0
        else:
            continue

        if y + h > usable_h:
            pages += 1
            y = h
        else:
            y += h
    return pages


def count_pdf_pages_via_libreoffice(docx_path: str) -> int | None:
    """Точно считает число страниц через LibreOffice (если установлен)."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmpdir, docx_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None
        pdf_path = os.path.join(tmpdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
        if not os.path.exists(pdf_path):
            return None
        with open(pdf_path, "rb") as f:
            raw = f.read()
        matches = re.findall(rb"/Type\s*/Page[^s]", raw)
        return len(matches) if matches else None

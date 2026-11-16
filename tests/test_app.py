import io
import zipfile

from pydantic import ValidationError
import pytest

from docx_builder.exporter import build_docx_bytes
from docx_builder.parser import parse_markup_to_blocks
from docx_builder.server.schemas import ParseRequest


def test_parse_markdown_blocks():
    sample = (
        "# Раздел 1\n"
        "Текст абзаца.\n\n"
        "| A | B |\n"
        "| --- | --- |\n"
        "| 1 | 2 |\n\n"
        "```java\nint x = 1;\n```\n\n"
        "---\n"
    )
    blocks = parse_markup_to_blocks(sample)
    assert [b["type"] for b in blocks] == ["heading", "paragraph", "table", "code", "page_break"]
    assert blocks[2]["headers"] == ["A", "B"]
    assert blocks[2]["rows"] == [["1", "2"]]


def test_docx_tables_have_cant_split_and_tbl_header():
    blocks = [
        {"type": "heading", "text": "Заголовок"},
        {"type": "table", "title": "Таблица", "headers": ["Колонка 1", "Колонка 2"], "rows": [["1", "2"]]},
        {"type": "code", "title": "Код", "code": "int a = 5;"},
    ]
    data, pages, _ = build_docx_bytes("Документ", "Подзаголовок", blocks, include_solutions=True, even_pages=True)
    assert pages % 2 == 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
        assert "w:cantSplit" in xml
        assert "w:tblHeader" in xml


def test_parse_request_rejects_oversized_payload():
    with pytest.raises(ValidationError):
        ParseRequest(raw_text="x" * 200_001)

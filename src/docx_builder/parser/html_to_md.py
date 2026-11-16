import re
from html.parser import HTMLParser


class _HtmlToMarkdownConverter(HTMLParser):
    """Переводит HTML-теги (h1-h4, p, b/strong, i/em, ul/ol/li, pre/code, table, blockquote, hr) в Markdown."""

    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []
        self.in_pre = False
        self.in_table = False
        self.list_stack: list[tuple[str, int]] = []
        self.row_cells: list[str] = []
        self.table_rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t in ("h1", "h2", "h3", "h4"):
            lvl = int(t[1])
            self.out.append(f"\n{'#' * lvl} ")
        elif t in ("p", "div", "br"):
            if not self.in_pre and not self.in_table:
                self.out.append("\n")
        elif t in ("b", "strong"):
            if not self.in_pre:
                self.out.append("**")
        elif t in ("i", "em"):
            if not self.in_pre:
                self.out.append("*")
        elif t == "ul":
            self.list_stack.append(("ul", 0))
            self.out.append("\n")
        elif t == "ol":
            self.list_stack.append(("ol", 0))
            self.out.append("\n")
        elif t == "li":
            if self.list_stack and self.list_stack[-1][0] == "ol":
                kind, cnt = self.list_stack[-1]
                cnt += 1
                self.list_stack[-1] = (kind, cnt)
                self.out.append(f"\n{cnt}. ")
            else:
                self.out.append("\n• ")
        elif t == "pre":
            self.in_pre = True
            self.out.append("\n```java\n")
        elif t == "code":
            if not self.in_pre:
                self.out.append("`")
        elif t == "blockquote":
            self.out.append("\n> ")
        elif t == "hr":
            self.out.append("\n---\n")
        elif t == "table":
            self.in_table = True
            self.table_rows = []
        elif t == "tr":
            self.row_cells = []
        elif t in ("td", "th"):
            self.out.append("\x00CELL\x00")

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in ("h1", "h2", "h3", "h4", "p", "div", "li", "blockquote"):
            if not self.in_pre and not self.in_table:
                self.out.append("\n")
        elif t in ("b", "strong"):
            if not self.in_pre:
                self.out.append("**")
        elif t in ("i", "em"):
            if not self.in_pre:
                self.out.append("*")
        elif t in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self.out.append("\n")
        elif t == "pre":
            self.in_pre = False
            self.out.append("\n```\n")
        elif t == "code":
            if not self.in_pre:
                self.out.append("`")
        elif t in ("td", "th"):
            full = "".join(self.out)
            idx = full.rfind("\x00CELL\x00")
            if idx != -1:
                cell_txt = full[idx + 6:].strip().replace("\n", " ")
                self.out = [full[:idx]]
                self.row_cells.append(cell_txt)
        elif t == "tr":
            if self.row_cells:
                self.table_rows.append(self.row_cells)
        elif t == "table":
            self.in_table = False
            if self.table_rows:
                self.out.append("\n")
                for r_i, row in enumerate(self.table_rows):
                    self.out.append("| " + " | ".join(row) + " |\n")
                    if r_i == 0:
                        self.out.append("| " + " | ".join(["---"] * len(row)) + " |\n")
                self.out.append("\n")

    def handle_data(self, data: str) -> None:
        self.out.append(data)

    def get_markdown(self) -> str:
        return "".join(self.out)


_HTML_TAG_RE = re.compile(
    r'<(?:h[1-4]|p|div|ul|ol|li|pre|code|table|b|strong|i|em|blockquote|hr)\b',
    re.IGNORECASE,
)


def html_to_markdown_if_needed(raw_text: str) -> str:
    """Конвертирует входной текст из HTML в Markdown, если обнаружены HTML-теги."""
    if _HTML_TAG_RE.search(raw_text):
        conv = _HtmlToMarkdownConverter()
        conv.feed(raw_text)
        return conv.get_markdown()
    return raw_text

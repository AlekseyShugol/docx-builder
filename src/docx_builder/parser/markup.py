import re

from .html_to_md import html_to_markdown_if_needed

_TASK_RE = re.compile(r'^(?:#{1,4}\s*)?(?:Задача\s*\d+[\.\):])\s*(.+)$', re.IGNORECASE)
_HEADING_RE = re.compile(r'^#{1,4}\s+(.+)$')
_HR_RE = re.compile(r'^(?:-{3,}|\*{3,}|_{3,})$')
_TABLE_SEP_RE = re.compile(r'^\|\s*[-:|\s]+\|$')


def clean_inline_markdown(text: str) -> str:
    """Убирает inline-разметку Markdown (**жирный**, *курсив*, `код`)."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text


def _normalize_table(raw_rows: list[list[str]]) -> dict:
    """Формирует блок таблицы с выровненным числом колонок."""
    col_count = max(len(r) for r in raw_rows)
    padded = [r + [""] * (col_count - len(r)) for r in raw_rows]
    return {
        "type": "table",
        "title": "",
        "headers": padded[0],
        "rows": padded[1:],
    }


def parse_markup_to_blocks(raw_text: str) -> list[dict]:
    """Разбирает Markdown или HTML в список структурированных блоков документа."""
    md_text = html_to_markdown_if_needed(raw_text)
    blocks: list[dict] = []

    lines = md_text.splitlines()
    i = 0
    n = len(lines)
    para_buf: list[str] = []

    def flush_paragraphs() -> None:
        if not para_buf:
            return
        cleaned: list[str] = []
        for ln in para_buf:
            s = ln.strip()
            if not s:
                continue
            if s.startswith("> "):
                s = "Примечание: " + s[2:].strip()
            elif re.match(r'^[-*]\s+', s):
                s = "• " + re.sub(r'^[-*]\s+', '', s)
            cleaned.append(clean_inline_markdown(s))
        if cleaned:
            blocks.append({"type": "paragraph", "text": "\n".join(cleaned)})
        para_buf.clear()

    while i < n:
        line = lines[i]
        s = line.strip()

        if s.startswith("```"):
            flush_paragraphs()
            lang = s[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            title_lbl = f"Листинг кода ({lang})" if lang else "Листинг кода"
            blocks.append({
                "type": "code",
                "title": title_lbl,
                "code": "\n".join(code_lines),
            })
            continue

        if s.startswith("|") and s.endswith("|"):
            flush_paragraphs()
            raw_rows: list[list[str]] = []
            while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                row_s = lines[i].strip()
                if not _TABLE_SEP_RE.match(row_s):
                    cells = [clean_inline_markdown(c.strip()) for c in row_s.strip("|").split("|")]
                    raw_rows.append(cells)
                i += 1
            if raw_rows:
                blocks.append(_normalize_table(raw_rows))
            continue

        if _HR_RE.match(s):
            flush_paragraphs()
            blocks.append({"type": "page_break"})
            i += 1
            continue

        if _TASK_RE.match(s):
            flush_paragraphs()
            task_title = clean_inline_markdown(s.lstrip("#").strip())
            i += 1
            cond, io_lines, hint, sol_lines = [], [], "", []
            in_task_code = False
            while i < n:
                nxt = lines[i]
                ns = nxt.strip()
                if not in_task_code and (_TASK_RE.match(ns) or _HEADING_RE.match(ns) or _HR_RE.match(ns)):
                    break
                if ns.startswith("```"):
                    in_task_code = not in_task_code
                    i += 1
                    continue
                if in_task_code:
                    sol_lines.append(nxt)
                elif ns:
                    clean_s = clean_inline_markdown(ns)
                    if re.match(r'^(?:Рекомендация|Подсказка|На что обратить внимание)\s*:', clean_s, re.I):
                        hint = re.sub(
                            r'^(?:Рекомендация|Подсказка|На что обратить внимание)\s*:\s*', '', clean_s, flags=re.I
                        )
                    elif re.match(r'^(?:Вход|Выход)\s*:', clean_s, re.I):
                        io_lines.append(clean_s)
                    else:
                        cond.append(clean_s)
                i += 1
            blocks.append({
                "type": "task",
                "title": task_title,
                "condition": "\n".join(cond),
                "io": "\n".join(io_lines),
                "hint": hint,
                "solution": "\n".join(sol_lines),
            })
            continue

        m_head = _HEADING_RE.match(s)
        if m_head:
            flush_paragraphs()
            blocks.append({
                "type": "heading",
                "text": clean_inline_markdown(m_head.group(1).strip()),
            })
            i += 1
            continue

        if not s:
            flush_paragraphs()
        else:
            para_buf.append(line)
        i += 1

    flush_paragraphs()
    return blocks

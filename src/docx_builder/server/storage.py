import copy
import json

from ..config import AUTOSAVE_PATH, EMPTY_DOC


def load_draft() -> dict:
    """Загружает последний автосохранённый документ с диска или возвращает пустой шаблон."""
    if AUTOSAVE_PATH.exists():
        try:
            with open(AUTOSAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("blocks"), list):
                return {
                    "title": str(data.get("title", "")),
                    "subtitle": str(data.get("subtitle", "")),
                    "blocks": data["blocks"],
                }
        except Exception:
            pass
    return copy.deepcopy(EMPTY_DOC)


def save_draft(data: dict) -> None:
    """Сохраняет черновик документа в JSON-файл."""
    AUTOSAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTOSAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

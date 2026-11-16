from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import Response

from ..config import DISABLE_SERVER_DRAFT, EMPTY_DOC
from ..exporter import build_docx_bytes
from ..parser import parse_markup_to_blocks
from .schemas import DocumentPayload, ExportRequest, ParseRequest
from .storage import load_draft, save_draft

router = APIRouter(prefix="/api", tags=["docx-builder"])


@router.get("/health")
def health() -> dict[str, str]:
    """Проверка доступности сервера."""
    return {"status": "ok"}


@router.get("/draft")
def get_draft() -> dict:
    """Возвращает сохранённый черновик документа (в серверном режиме отключён для изоляции)."""
    if DISABLE_SERVER_DRAFT:
        return dict(EMPTY_DOC)
    return load_draft()


@router.put("/draft")
def put_draft(payload: DocumentPayload) -> dict[str, bool]:
    """Сохраняет черновик документа на сервер (если не отключён)."""
    if not DISABLE_SERVER_DRAFT:
        save_draft(payload.model_dump())
    return {"ok": True}


@router.post("/parse")
def parse_markup(req: ParseRequest) -> dict[str, list[dict]]:
    """Преобразует Markdown или HTML в список блоков документа."""
    return {"blocks": parse_markup_to_blocks(req.raw_text)}


@router.post("/export")
def export_docx_endpoint(req: ExportRequest) -> Response:
    """Генерирует .docx и отдаёт его как скачиваемый файл."""
    data, pages, filler_added = build_docx_bytes(
        doc_title=req.title,
        doc_subtitle=req.subtitle,
        blocks=req.blocks,
        include_solutions=req.include_solutions,
        even_pages=req.even_pages,
    )
    raw_name = (req.title.strip() or "document")[:64]
    safe_ascii = "".join(c if c.isascii() and (c.isalnum() or c in "-_ ") else "_" for c in raw_name).strip() or "document"
    utf8_name = quote(f"{raw_name}.docx")

    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_ascii}.docx"; filename*=UTF-8\'\'{utf8_name}',
            "X-Docx-Pages": str(pages),
            "X-Docx-Even-Filler": "1" if filler_added else "0",
            "Access-Control-Expose-Headers": "X-Docx-Pages, X-Docx-Even-Filler, Content-Disposition",
        },
    )

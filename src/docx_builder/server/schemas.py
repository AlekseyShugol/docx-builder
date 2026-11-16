from typing import Any

from pydantic import BaseModel, Field

from ..config import MAX_BLOCKS_COUNT, MAX_RAW_MARKUP_LEN


class DocumentPayload(BaseModel):
    title: str = Field(default="", max_length=500)
    subtitle: str = Field(default="", max_length=500)
    blocks: list[dict[str, Any]] = Field(default_factory=list, max_length=MAX_BLOCKS_COUNT)


class ParseRequest(BaseModel):
    raw_text: str = Field(default="", max_length=MAX_RAW_MARKUP_LEN)


class ExportRequest(DocumentPayload):
    include_solutions: bool = True
    even_pages: bool = True

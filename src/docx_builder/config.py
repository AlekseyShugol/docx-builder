import os
import re
from pathlib import Path

AUTOSAVE_PATH = Path.home() / ".word_builder_clean.json"

DEFAULT_HOST = os.getenv("DOCX_BUILDER_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("DOCX_BUILDER_PORT", "8000"))

DISABLE_SERVER_DRAFT = os.getenv("DOCX_BUILDER_DISABLE_SERVER_DRAFT", "0") == "1"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("DOCX_BUILDER_CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

MAX_RAW_MARKUP_LEN = 200_000
MAX_BLOCKS_COUNT = 500

JAVA_KEYWORDS = {
    "public", "private", "protected", "static", "final", "void", "int", "double",
    "char", "boolean", "byte", "short", "long", "float", "if", "else", "for",
    "while", "do", "switch", "case", "default", "break", "continue", "return",
    "new", "throw", "throws", "true", "false", "null", "class", "import", "package",
}

TOKEN_PATTERN = re.compile(r'(//.*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\w+|\s+|.)')

EMPTY_DOC = {
    "title": "",
    "subtitle": "",
    "blocks": [],
}

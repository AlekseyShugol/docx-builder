import argparse

from .config import DEFAULT_HOST, DEFAULT_PORT
from .server import run_server


def main() -> None:
    """Точка входа CLI для запуска веб-сервера Docx Builder."""
    parser = argparse.ArgumentParser(description="Docx Builder — веб-редактор документов .docx")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Хост сервера (по умолчанию {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Порт сервера (по умолчанию {DEFAULT_PORT})")
    parser.add_argument("--no-browser", action="store_true", help="Не открывать браузер автоматически")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, open_browser=not args.no_browser)

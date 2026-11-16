import socket
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..config import CORS_ORIGINS, DEFAULT_HOST, DEFAULT_PORT
from .routes import router

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def create_app() -> FastAPI:
    """Создаёт и настраивает FastAPI-приложение."""
    app = FastAPI(title="Docx Builder", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    def serve_index() -> FileResponse:
        return FileResponse(_WEB_DIR / "index.html")

    @app.get("/manifest.webmanifest", include_in_schema=False)
    def serve_manifest() -> FileResponse:
        return FileResponse(_WEB_DIR / "manifest.webmanifest", media_type="application/manifest+json")

    @app.get("/sw.js", include_in_schema=False)
    def serve_sw() -> FileResponse:
        return FileResponse(_WEB_DIR / "sw.js", media_type="application/javascript")

    app.mount("/static", StaticFiles(directory=str(_WEB_DIR)), name="static")
    return app


def _find_free_port(host: str, preferred_port: int) -> int:
    for port in range(preferred_port, preferred_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) != 0:
                return port
    return preferred_port


def _open_browser_when_ready(url: str) -> None:
    time.sleep(0.6)
    webbrowser.open(url)


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    open_browser: bool = True,
) -> None:
    """Запускает локальный сервер и открывает веб-редактор в браузере."""
    actual_port = _find_free_port(host, port)
    url = f"http://{host}:{actual_port}"

    if open_browser:
        threading.Thread(target=_open_browser_when_ready, args=(url,), daemon=True).start()

    print(f"Docx Builder запущен: {url}")
    uvicorn.run(create_app(), host=host, port=actual_port, log_level="warning")

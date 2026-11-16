"""FastAPI-сервер и HTTP API для редактора документов."""

from .app import create_app, run_server

__all__ = ["create_app", "run_server"]

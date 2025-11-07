"""
Main entry point for the Telegram service.

This module imports the FastAPI application from the new structure.
It's maintained for backward compatibility with existing deployment scripts.

For new deployments, use:
    uvicorn app.main:app --host 0.0.0.0 --port 8001
    granian --interface asgi app.main:app --host 0.0.0.0 --port 8001
"""

from app.main import app

__all__ = ["app"]
